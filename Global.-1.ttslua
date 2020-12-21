--[[ Lua code. See documentation: http://berserk-games.com/knowledgebase/scripting/ --]]

function getHelperClient(helperObjectName)
    local function getHelperObject()
        for _, object in ipairs(getAllObjects()) do
            if object.getName() == helperObjectName then return object end
        end
        error('missing object "' .. helperObjectName .. '"')
    end
    -- Nested tables are considered cross script.  Make a local copy.
    local function copyTable(t)
        if t and type(t) == 'table' then
            local copy = {}
            for k, v in pairs(t) do
                copy[k] = type(v) == 'table' and copyTable(v) or v
            end
            t = copy
        end
        return t
    end
    local helperObject = false
    local function getCallWrapper(functionName)
        helperObject = helperObject or getHelperObject()
        if not helperObject.getVar(functionName) then error('missing ' .. helperObjectName .. '.' .. functionName) end
        return function(parameters) return copyTable(helperObject.call(functionName, parameters)) end
    end
    return setmetatable({}, { __index = function(t, k) return getCallWrapper(k) end })
end

local _deckHelper = getHelperClient('TI4_DECK_HELPER')
local _factionHelper = getHelperClient('TI4_FACTION_HELPER')
local _setupHelper = getHelperClient('TI4_SETUP_HELPER')
local _systemHelper = getHelperClient('TI4_SYSTEM_HELPER')
local _zoneHelper = getHelperClient('TI4_ZONE_HELPER')

--- Randomize to split/join stacks and replace units with tokens.
-- @author original by GarnetBear October 18, 2019
-- @author updated by Darrell May 2020 to merge groups.

-- Map from replaceable object name to bag name.
local REPLACE_OBJECTNAME_TO_BAGNAME = {
    ['x1 Fighter Token'] = 'x1 Fighter Tokens Bag',
    ['x3 Fighter Token'] = 'x3 Fighter Tokens Bag',
    ['x1 Infantry Token'] = 'x1 Infantry Tokens Bag',
    ['x3 Infantry Token'] = 'x3 Infantry Tokens Bag',
    ['x1 Commodities/Tradegoods'] = 'x1 Commodities/Tradegoods Bag',
    ['x3 Commodities/Tradegoods'] = 'x3 Commodities/Tradegoods Bag',
    ['$COLOR Fighter'] = '$COLOR Fighter',
    ['$COLOR Infantry'] = '$COLOR Infantry'
}

-- Replace consumed items with produced items.  Repeatable entries happen as
-- much as possible from the input, and ONLY IF no repeatable do the first
-- non-repeatable (eagerly group, cautiously break apart).  Plastic color is
-- mandated by the player doing the 'r' randomizing for safety/simplicity.
local REPLACE_RULES = {
    {
        repeatable = true,
        consume = { count = 3, items = { 'x1 Fighter Token', '$COLOR Fighter' }},
        produce = { item = 'x3 Fighter Token' },
    },
    {
        repeatable = true,
        consume = { count = 3, items = { 'x1 Infantry Token', '$COLOR Infantry' }},
        produce = { item = 'x3 Infantry Token' },
    },
    {
        repeatable = true,
        splitFaceDown = true,
        consume = { count = 3, item = 'x1 Commodities/Tradegoods' },
        produce = { item = 'x3 Commodities/Tradegoods' },
    },
    {
        consume = { item = 'x3 Fighter Token' },
        produce = { count = 3, item = 'x1 Fighter Token' },
    },
    {
        consume = { item = 'x3 Infantry Token' },
        produce = { count = 3, item = 'x1 Infantry Token' },
    },
    {
        splitFaceDown = true,
        consume = { item = 'x3 Commodities/Tradegoods' },
        produce = { count = 3, item = 'x1 Commodities/Tradegoods' },
    },
    {
        consume = { item = 'x1 Fighter Token' },
        produce = { item = '$COLOR Fighter' },
    },
    {
        consume = { item = 'x1 Infantry Token' },
        produce = { item = '$COLOR Infantry' },
    },
    {
        consume = { item = '$COLOR Fighter' },
        produce = { item = 'x1 Fighter Token' },
    },
    {
        consume = { item = '$COLOR Infantry' },
        produce = { item = 'x1 Infantry Token' },
    },
}

local _pendingReplace = assert(not _pendingReplace) and false

-- Get absolute bag name from $COLOR-allowed item name.
local function _getBag(itemName, playerColor)
   assert(type(itemName) == 'string' and type(playerColor) == 'string')

   -- Item name $COLOR points to (potentially with $COLOR) bag name.
   -- Replace any bag name $COLOR for the absolute object name.
   local bagName = REPLACE_OBJECTNAME_TO_BAGNAME[itemName]
   assert(bagName, 'no bag for ' .. itemName)
   bagName = string.gsub(bagName, '$COLOR', playerColor)

   -- Remember bags for faster future lookups.
   local bagGuidCache = REPLACE_OBJECTNAME_TO_BAGNAME._bagGuidCache
   if not bagGuidCache then
       bagGuidCache = {}
       REPLACE_OBJECTNAME_TO_BAGNAME._bagGuidCache = bagGuidCache
   end
   local bagGuid = bagGuidCache[bagName]
   local bag = bagGuid and getObjectFromGUID(bagGuid)
   if not bag then
       for _, object in ipairs(getAllObjects()) do
           if (object.tag == 'Bag' or object.tag == 'Infinite') and object.getName() == bagName then
               bagGuidCache[bagName] = object.getGUID()
               bag = object
               break
           end
       end
   end
   assert(bag)
   return bag
end

local originalOnObjectRandomize = onObjectRandomize
function onObjectRandomize(object, playerColor)
    assert(type(object) == 'userdata' and type(playerColor) == 'string')

    if originalOnObjectRandomize then
        originalOnObjectRandomize(object, playerColor)
    end

    -- Only swap tokens/units, not unit bags.
    if object.tag == 'Bag' then
        return
    end

    -- Get consume items from entries (does not remove them from entries).
    -- @param rule: REPLACE_RULES value.
    -- @param entries: MAP from index to entry, may have holes!
    -- @param splitFaceDown boolean: if true, generate separate face up/face down results.
    -- @return consumable, consumableFaceDown: list of entries map keys to consumable entries.
    local function getConsumable(rule, entries)
        assert(rule.consume and type(entries) == 'table')
        local consumable, consumableFaceDown = {}, {}

        -- For multi-item rules add in item list order (prefer token to plastic when grouping).
        for _, consumeName in ipairs(rule.consume.items or { rule.consume.item }) do
            for i, entry in pairs(entries) do
                if consumeName == entry.consumeName then
                    if rule.splitFaceDown and entry.object.is_face_down then
                        table.insert(consumableFaceDown, i)
                    else
                        table.insert(consumable, i)
                    end
                end
            end
        end
        return consumable, consumableFaceDown
    end

    -- Consume once, removing consumed entries from collection.
    -- @param rule: REPLACE_RULES value.
    -- @param entries: MAP from index to entry, may have holes!  Gets mutated.
    -- @param consumable: list of entries map keys to consumable entries.
    -- @param boolean: did consume happen?
    local function doConsume(rule, entries, consumable, playerColor)
        assert(rule.consume and type(entries) == 'table' and type(consumable) == 'table' and type(playerColor) == 'string')

        -- Verify consume units.
        if #consumable < (rule.consume.count or 1) then
            return false
        end

        -- Verify produce units are available.
        local produceBag = _getBag(rule.produce.item, playerColor)
        if not produceBag then
            error('itemName=' .. rule.produce.item .. ' color=' .. playerColor)
        end
        if produceBag.tag == 'Bag' and produceBag.getQuantity() < (rule.produce.count or 1) then
            return false
        end

        -- Om nom nom!
        local consumeCounts = {}
        local position, isFaceDown
        for _ = 1, (rule.consume.count or 1) do
            local i = table.remove(consumable, 1)  -- consume in list order
            local entry = entries[i]
            entries[i] = nil
            local consumeObject = entry.object
            local consumeBag = _getBag(entry.consumeName, playerColor)
            consumeCounts[consumeObject.getName()] = (consumeCounts[consumeObject.getName()] or 0) + 1
            position = position or consumeObject.getPosition()
            isFaceDown = consumeObject.is_face_down
            consumeBag.putObject(consumeObject)
        end

        -- Thppt!
        local produceCounts = {}
        for _ = 1, (rule.produce.count or 1) do
            position.z = position.z + 0.5
            position.y = position.y + 0.5
            local produceObject = produceBag.takeObject({
                position = position,
                rotation = (rule.splitFaceDown and isFaceDown and {180,0,0}) or {0,0,0},
            })
            produceCounts[produceObject.getName()] = (produceCounts[produceObject.getName()] or 0) + 1
        end

        -- Report.
        local function getMessage(nameCounts)
            local message = {}
            for name, count in pairs(nameCounts) do
                if #message > 0 then table.insert(message, ', ') end
                if count > 1 then table.insert(message, count .. ' ') end
                table.insert(message, '“' .. name .. '”')
            end
            return table.concat(message, '')
        end
        --print('(R) { ' .. getMessage(consumeCounts) .. ' } -> { ' .. getMessage(produceCounts) .. ' }')

        return true
    end

    local function delayedReplace()
        for color, entries in pairs(_pendingReplace) do
            local didConsume = false
            for _, rule in ipairs(REPLACE_RULES) do
                if rule.repeatable then
                    -- Do all repeatable rules as many times as possible.
                    local consumable1, consumable2 = getConsumable(rule, entries)
                    while doConsume(rule, entries, consumable1, color) do
                        didConsume = true
                    end
                    while doConsume(rule, entries, consumable2, color) do
                        didConsume = true
                    end
                elseif not didConsume then
                    -- If singleton and nothing consumed yet, consume ONLY FIRST APPLICABPLE.
                    local consumable1, consumable2 = getConsumable(rule, entries)
                    didConsume = doConsume(rule, entries, consumable1, color)
                    if didConsume then
                        break
                    end
                    didConsume = doConsume(rule, entries, consumable2, color)
                    if didConsume then
                        break
                    end
                end
            end
        end
        _pendingReplace = false
    end

    -- If this looks like a replace candidate, queue for processing next frame.
    -- (Waiting a frame lets randomizing a group gather all peers.)
    local consumeName = string.gsub(object.getName(), playerColor, '$COLOR')
    if REPLACE_OBJECTNAME_TO_BAGNAME[consumeName] then
        if not _pendingReplace then
            _pendingReplace = {}
            Wait.frames(delayedReplace, 2)
        end
        local byColor = _pendingReplace[playerColor]
        if not byColor then
            byColor = {}
            _pendingReplace[playerColor] = byColor
        end
        table.insert(byColor, { object = object, consumeName = consumeName, playerColor = playerColor })
    end
end

-------------------------------------------------------------------------------

local KEY_INDEX_TO_TOKEN = {
    [1] = 'x1 Commodities/Tradegoods',
    [2] = 'x1 Fighter Token',
    [3] = 'x1 Infantry Token',
}

local _graveyardGuid = false
function _getGraveyard()
    local bag = _graveyardGuid and getObjectFromGUID(_graveyardGuid)
    if not bag then
        for _, object in ipairs(getAllObjects()) do
            if object.tag == 'Bag' and string.match(object.getName(), '^TI4 Graveyard') then
                _graveyardGuid = object.getGUID()
                bag = object
                break
            end
        end
    end
    return bag
end

function onScriptingButtonUp(index, playerColor)
    assert(type(index) == 'number' and type(playerColor) == 'string')

    -- Spectators cannot use these.  If there are multiple spectators
    -- do not know which pressed the key; not safe to move camera.
    if playerColor == 'Grey' then
        return
    end

    local tokenBagName = KEY_INDEX_TO_TOKEN[index]
    if tokenBagName then
        local pointerPosition = Player[playerColor].getPointerPosition()
        local bag = _getBag(tokenBagName, playerColor)
        bag.takeObject({
            position = pointerPosition,
            smooth = true
        })
    end

    -- 4=roller, 5=active system, 6=map, 7=scoreboard, 8=votes, 9=player zone.
    local function _getByName(name)
        for i, obj in ipairs(getAllObjects()) do
            if obj.getName() == name then
                return obj
            end
        end
    end
    local function _closestRoller(p0)
        local best = false
        local bestDsq = false
        for _, object in ipairs(getAllObjects()) do
            if string.match(object.getName(), '^TI4 MultiRoller') then
                local p1 = object.getPosition()
                local dSq = (p0.x - p1.x)^2 + (p0.z - p1.z)^2
                if (not bestDsq) or (dSq < bestDsq) then
                    best = object
                    bestDsq = dSq
                end
            end
        end
        return best
    end
    if index == 4 then
        -- Roller
        local zoneAttr = _zoneHelper.zoneAttributes(playerColor)
        local roller = zoneAttr and _closestRoller(zoneAttr.center)
        if zoneAttr and roller then
            Player[playerColor].lookAt({
                position = roller.getPosition(),
                pitch    = 75,
                yaw      = zoneAttr.rotation.y + 180,
                distance = 20,
            })
        end
    elseif index == 5 then
        -- Active system
        local zoneAttr = _zoneHelper.zoneAttributes(playerColor)
        local system = _systemHelper.getLastActivatedSystem()
        local systemObject = system and getObjectFromGUID(system.guid)
        if zoneAttr and systemObject then
            Player[playerColor].lookAt({
                position = systemObject.getPosition(),
                pitch    = 60,
                yaw      = zoneAttr.rotation.y + 180,
                distance = 10,
            })
        elseif not systemObject then
            printToColor('No active system', playerColor)
        end
    elseif index == 6 then
        -- Map
        local zoneAttr = _zoneHelper.zoneAttributes(playerColor)
        local extraRings = _zoneHelper.getExtraRings()
        if zoneAttr then
            Player[playerColor].lookAt({
              position = {0,0,0},
              pitch    = 75,
              yaw      = zoneAttr.rotation.y + 180,
              distance = 45 + (extraRings or 0) * 12,
            })
        end
    elseif index == 7 then
        -- Scoreboard
        local scoreBoardObj = _getByName('Scoreboard')
        local secretsMatObj = _getByName('Secrets Mat')
        if scoreBoardObj and secretsMatObj then
            local p0 = scoreBoardObj.getPosition()
            local p1 = secretsMatObj.getPosition()
            local p = { x = (p0.x + p1.x) / 2, y = (p0.y + p1.y) / 2, z = (p0.z + p1.z) / 2, }
            Player[playerColor].lookAt({
              position = p,
              pitch    = 90,
              yaw      = scoreBoardObj.getRotation().y + 180,
              distance = 30,
            })
        end
    elseif index == 8 then
        -- Votes
        local voteCounter = _getByName(playerColor .. ' Player Votes')
        if voteCounter then
          Player[playerColor].lookAt({
              position = voteCounter.getPosition(),
              pitch    = 60,
              yaw      = voteCounter.getRotation().y,
              distance = 30,
            })
        end
    elseif index == 9 then
        -- Player zone
        local zoneAttr = _zoneHelper.zoneAttributes(playerColor)
        if zoneAttr then
            Player[playerColor].lookAt({
              position = zoneAttr.center,
              pitch    = 60,
              yaw      = zoneAttr.rotation.y+180,
              distance = 45,
            })
        end
    end

    -- Index 10 is '0'.  Throw any held object(s) into the graveyard.
    -- Could use getHoverObject but this feels like it requires more intention.
    if index == 10 then
        local holding = Player[playerColor].getHoldingObjects()
        local graveyard = _getGraveyard()
        if holding and #holding > 0 and graveyard then
            printToAll(playerColor .. ' quick trashing ' .. (#holding) .. ' items.', playerColor)
            for _, object in ipairs(holding) do
                graveyard.putObject(object)
            end
        end
    end
end

-------------------------------------------------------------------------------


--- Shuffle decks when the game first starts.
-- @author Darrell
local originalOnLoad = onLoad
function onLoad(saveState)
    if originalOnLoad then
        originalOnLoad(saveState)
    end

    local shuffleSet = {
        ['Public Objectives I'] = 'Deck',
        ['Public Objectives II'] = 'Deck',
        ['Secret Objectives'] = 'Deck',
        ['Agenda'] = 'Deck',
        ['Actions'] = 'Deck',
        ['Pick a Faction to Play'] = 'Bag',
        ['Blue Planet Tiles'] = 'Bag',
        ['Red Anomaly Tiles'] = 'Bag',
        ['Randomize Seats'] = 'Bag',
        ['Cultural Exploration'] = 'Deck',
        ['Industrial Exploration'] = 'Deck',
        ['Hazardous Exploration'] = 'Deck',
        ['Frontier Exploration'] = 'Deck',
        ['Relics'] = 'Deck',
    }
    local toShuffle = {}
    for _, object in ipairs(getAllObjects()) do
        local name = object.getName()
        local tag = object.tag
        if tag == 'Bag' and string.match(name, ' Command Tokens Bag$') then
            return  -- loaded a game in progress, abort!
        end
        local expectTag = shuffleSet[name]
        if expectTag and tag == expectTag then
            table.insert(toShuffle, object)
        end
    end
    local shuffled = {}
    for _, object in ipairs(toShuffle) do
        object.shuffle()
        table.insert(shuffled, object.getName())
    end
    if #shuffled > 0 then
        printToAll('Shuffled: ' .. table.concat(table.sort(shuffled), ', ') .. '.')
    end
end

-------------------------------------------------------------------------------

function genericFollow(player, option, id)
    broadcastToAll(player.steam_name .. " uses " .. option .. ".", player.color)
    sendOnStrategyCardButtonClicked(player.color, option, id)
end

function notFollow(player, option, id)
    broadcastToAll(player.steam_name .. " does not use " .. option .. ".", player.color)
    sendOnStrategyCardButtonClicked(player.color, option, id)
end

function genericSilent(player, option, id)
    sendOnStrategyCardButtonClicked(player.color, option, id)
end

function closeMenu(player, menu, id)
    local vis = UI.getAttribute(menu, "visibility")
    if vis == nil or vis == "" then
        local seatedPlayers = getSeatedPlayers()
        for p, player in pairs(seatedPlayers) do
            if vis == nil or vis == "" then
                vis = player
            else
                vis = vis .. "|" .. player
            end
        end
    end
    local i, j = string.find(vis, player.color)
    local l = string.len(vis)
    if i ~= nil and j ~= nil then
        if i == 1 then
            if j == l then
                newVis = ""
            else
                newVis = string.sub(vis,j+2,l)
            end
        else
            if j == l then
                newVis = string.sub(vis,1,i-2)
            else
                newVis = string.sub(vis,1,i-1) .. string.sub(vis,j+2,l)
            end
        end
    end
    if newVis == "" then
        UI.setAttribute(menu, "active", false)
        broadcastToAll("All players have responded", "Black")
    end
    UI.setAttribute(menu, "visibility", newVis)
    sendOnStrategyCardButtonClicked(player.color, menu, id)
end

function leadershipSelected(player, option, id)
    broadcastToAll(player.steam_name .. " uses Leadership to gain " .. option .. " command tokens.", player.color)
    sendOnStrategyCardButtonClicked(player.color, option, id)
end

function politicsPrimary(player, option, id)
    broadcastToAll(player.steam_name .. " places " .. option .. " of the agenda deck.", player.color)
    sendOnStrategyCardButtonClicked(player.color, option, id)
end

function constructionPrimary(player, option, id)
    broadcastToAll(player.steam_name .. " uses Construction Primary to build " .. option .. ".", player.color)
    sendOnStrategyCardButtonClicked(player.color, option, id)
end

function constructionSecondary(player, option, id)
    broadcastToAll(player.steam_name .. " uses Construction Secondary to build " .. option .. ".", player.color)
    sendOnStrategyCardButtonClicked(player.color, option, id)
end

function tradeSelected(player, option, id)
    broadcastToAll(player.steam_name .. " uses Trade to refresh " .. option .. "'s commodities.", option)
    sendOnStrategyCardButtonClicked(player.color, option, id)
end

function pickTech(player, option, id)
    broadcastToAll(player.steam_name .. " researches " .. option .. ".", player.color)
    sendOnStrategyCardButtonClicked(player.color, option, id)
end

function sendOnStrategyCardButtonClicked(player, value, strategyCard)
    local handler = 'onStrategyCardButtonClicked'
    local listeners = {}
    for _, object in ipairs(getAllObjects()) do
        if object.getVar(handler) then
            table.insert(listeners, object.getGUID())
        end
    end
    if #listeners > 0 then
        local params = {
            player = player,
            strategyCard = strategyCard,
            value = value
        }
        for i, guid in ipairs(listeners) do
            local function callHandler()
                local listener = getObjectFromGUID(guid)
                if listener then
                    listener.call(handler, params)
                end
            end
            Wait.frames(callHandler, i)
        end
    end
end

-------------------------------------------------------------------------------

-- Exclusive bags are bags where all entries share the bag name, such as units.
-- Use 'filter' to prevent other objects from entering those bags.
-- @author Darrell
local exclusiveBagSet = {}

local originalFilterObjectEnterContainer = filterObjectEnterContainer
function filterObjectEnterContainer(container, enterObject)
    local result = true

    if originalFilterObjectEnterContainer then
        result = result and originalFilterObjectEnterContainer(container, enterObject)
    end

    local bagName = container.getName()
    local entryName = enterObject.getName()
    local exclusiveBag = string.len(bagName) > 0 and exclusiveBagSet[bagName]
    result = result and (not exclusiveBag or bagName == entryName)

    -- Also reject wrong items into the command tokens bags.
    if string.find(bagName, 'Command Tokens Bag') then
        entryName = string.gsub(entryName, '-', '%%-')
        result = result and string.find(bagName, entryName)
    end

    return result
end

-- Also reorient units upright when leaving a unit bag.
local originalOnObjectLeaveContainer = onObjectLeaveContainer
function onObjectLeaveContainer(container, leaveObject)
    if originalOnObjectLeaveContainer then
        originalOnObjectLeaveContainer(container, leaveObject)
    end
    local name = leaveObject.getName()
    if string.len(name) > 0 and exclusiveBagSet[name] then
        leaveObject.setRotation(container.getRotation())
    end
end

local UNIT_NAMES = {
    'Infantry',
    'Fighter',
    'Space Dock',
    'PDS',
    'Carrier',
    'Destroyer',
    'Cruiser',
    'Dreadnought',
    'War Sun',
    'Flagship',
}

local originalOnLoad = onLoad
function onLoad(saveState)
    if originalOnLoad then
        originalOnLoad(saveState)
    end
    exclusiveBagSet = {}
    for _, color in ipairs(Player.getColors()) do
        for _, unitName in ipairs(UNIT_NAMES) do
            exclusiveBagSet[color .. ' ' .. unitName] = true
        end
    end
    for _, faction in pairs(_factionHelper.allFactions(true)) do
        if faction.flagship then
            exclusiveBagSet[faction.flagship] = true
        end
    end
end

-------------------------------------------------------------------------------

-- Report when taking or putting command tokens.
-- @author Darrell

local _ctTransactions = assert(_ctTransactions == nil) and {}
local _ctWaitId = assert(_ctWaitId == nil) and false

local function reportCommandTokenTransaction(container, object, quantity)
    local isCommandTokenBag = string.match(container.getName(), 'Command Tokens Bag$')
    local isCommandToken = string.match(object.getName(), 'Command Token$')
    if not isCommandToken or not isCommandTokenBag then
        return
    end

    -- Keep deposit and withdrawl transactions separate.  During clean up
    -- a player will deposit tokens from the map, AND withdraw 2 (or 3).
    local name = object.getName()
    local type = (quantity > 0) and 'Deposited' or 'Withdrew'
    local transactions = _ctTransactions[name]
    if not transactions then
        transactions = {}
        _ctTransactions[name] = transactions
    end
    transactions[type] = (transactions[type] or 0) + math.abs(quantity)

    -- Wait before reporting in case withdrawing or depositing several.
    -- Restart the clock on each transaction.
    local function delayedReport()
        _ctWaitId = false
        for name, transactions in pairs(_ctTransactions) do
            local message = false
            local total = 0
            for type, quantity in pairs(transactions) do
                if not message then
                    message = type .. ' ' .. quantity
                else
                    message = message .. ', ' .. string.lower(type) .. ' ' .. quantity
                end
                total = total + quantity
            end
            if total > 0 then
                message = message .. ' ' .. name .. (total > 1 and 's' or '')
                printToAll(message)
            end
        end
        _ctTransactions = {}
    end
    if _ctWaitId then
        Wait.stop(_ctWaitId)
    end
    _ctWaitId = Wait.time(delayedReport, 5)
end

local originalOnObjectLeaveContainer = onObjectLeaveContainer
function onObjectLeaveContainer(container, leaveObject)
    if originalOnObjectLeaveContainer then
        originalOnObjectLeaveContainer(container, leaveObject)
    end
    reportCommandTokenTransaction(container, leaveObject, -1)
end

local originalOnObjectEnterContainer = onObjectEnterContainer
function onObjectEnterContainer(container, enterObject)
    if originalOnObjectEnterContainer then
        originalOnObjectEnterContainer(container, enterObject)
    end
    reportCommandTokenTransaction(container, enterObject, 1)
end

-------------------------------------------------------------------------------

local function _help(clickerColor)
    printToColor(table.concat({
        '!help supported messages:',
        '  !COLOR : announces whisper to COLOR (use "red", etc, for COLOR).',
        '  !tealme : change to the teal seat (can see !COLOR whispers).',
        '  !seats : swap seated players into random seats (only works before faction unpack).',
        'numpad keys:',
        '  6 : view galaxy map.',
        '  7 : view score area.',
        '  8 : view agenda phase area.',
        '  9 : view player zone.',
        '  0 : throw any HELD objects into the graveyard bag.',
    }, '\n'), clickerColor, 'Yellow')
end

local function _randomizeSeats(clickerColor)
    broadcastToAll(clickerColor .. ' used !seats to swap SEATED players into random seats.', 'Yellow')
    if clickerColor == 'Grey' then
        broadcastToAll('Spectators cannot swap seats', 'Yellow')
        return
    end
    for color, faction in pairs(_factionHelper.allFactions()) do
        broadcastToAll('Cannot swap seats after unpacking any factions', 'Yellow')
        return
    end

    local zoneColorSet = {}
    for _, zoneColor in ipairs(_zoneHelper.zones()) do
        zoneColorSet[zoneColor] = true
    end

    local players = {}
    local colors = {}
    for _, player in ipairs(Player.getPlayers()) do
        if zoneColorSet[player.color] then
            table.insert(players, player)
            table.insert(colors, player.color)
            player.changeColor('Grey')
        end
    end
    math.randomseed(os.time())
    for _, player in ipairs(players) do
        player.changeColor(table.remove(colors, math.random(#colors)))
    end
end

--- Use "!color message" to send an announced whisper.  Prints a message to
-- everyone else that the whisper happened, then sends whisper to the target.
-- Note that normal "/color message" whispers still work as before.
-- @author Darrell
local orginalOnChat = onChat
function onChat(message, srcPlayer)
    if orginalOnChat and not orginalOnChat(message, srcPlayer) then
        return false -- originial suppressed message
    end

    if string.lower(message) == '!tealme' then
        if srcPlayer.admin or srcPlayer.promoted then
            srcPlayer.changeColor('Teal')
        else
            printToAll('!tealme failed for ' .. srcPlayer.color .. ', must be promoted to use', 'Teal')
        end
        return false
    end

    if string.lower(message) == '!seats' then
        _randomizeSeats(srcPlayer.color)
        return false
    end

    if string.lower(message) == '!help' then
        _help(srcPlayer.color)
        return false
    end

    local colorSet = {}
    for _, color in ipairs(getSeatedPlayers()) do
        colorSet[color] = true
    end

    -- The real function throws an error on invalid input.
    local function safeColorToHex(color)
        if colorSet[color] then
            return Color.toHex(Color.fromString(color))
        end
        return 'ffffff'
    end

    local srcColor = srcPlayer.color
    local srcName = srcPlayer.steam_name
    local srcHex = safeColorToHex(srcColor)
    local msgHex = 'ffffff'
    local dstColor, message = string.match(message, '^!(%a+) (.+)')

    if dstColor then
        dstColor = dstColor:sub(1,1):upper()..dstColor:sub(2):lower()
        local dstHex = safeColorToHex(dstColor)

        local publicMessage = table.concat({
            '[' .. msgHex .. ']!Whisper: ',
            '[' .. srcHex .. ']' .. srcColor,
            ' ',
            '[' .. msgHex .. ']->',
            ' ',
            '[' .. dstHex .. ']' .. dstColor,
        }, '')

        local privateMessage = table.concat({
            '[' .. dstHex .. ']<' .. dstColor .. '>',
            ' ',
            '[' .. srcHex .. ']' .. srcName .. ':',
            ' ',
            '[' .. msgHex .. ']' .. message
        }, '')

        if not colorSet[dstColor] then
            printToColor('No one is playing as ' .. dstColor, srcColor, srcColor)
        else
            printToAll(publicMessage)
            printToColor(privateMessage, srcColor, srcColor)
            if dstColor ~= srcColor then
                printToColor(privateMessage, dstColor, srcColor)
            end
            if colorSet['Teal'] and srcColor ~= 'Teal' and dstColor ~= 'Teal' then
                printToColor(privateMessage, 'Teal', srcColor)
            end
        end
        return false
    end
    return true
end

--- Route draw X cards to deck helper for dealing.
function onObjectNumberTyped(object, playerColor, number)
    assert(type(object) == 'userdata' and type(playerColor) == 'string' and type(number) == 'number')
    -- Only intercept when over a deck, not if it is the last card.  Why? The
    -- card might be face down on the table as part of a player transaction,
    -- do not attempt to differentiate that from being in the deck locaiton.
    if object.tag == 'Deck' and _deckHelper.getDeck(object.getName()) == object.getGUID() then
        _deckHelper.deal({
            deck = object.getName(),
            color = playerColor,
            count = number
        })
        return true  -- stop TTS from dealing the card(s)
    end
end