# The TI4-TTS mod is now https://github.com/darrellanderson/TI4-TTS

# A note about #include

Atom offers a great #include shortcut to insert one ttslua file into another,
injecting the file when you push to TTS and replacing it with the include when
loading it back.  Nice!  ... except it does no checking.  If you were to create
an object with includes it would work, but if someone else were to load it they
would get a file with an include it in pointing to a missing file.

I use the InlineIncludes.py tool to create final versions, doing the same job
but with notation Atom does not understand to prevent it from attempting to
unwind the include if someone else looks at the file.

Moreover, the StripTests.py tool pulls out most of the testing code for release.
