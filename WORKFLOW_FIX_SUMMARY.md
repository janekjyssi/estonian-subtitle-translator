"""
SUBTITLE TRANSLATION WORKFLOW FIX - SUMMARY
============================================

PROBLEM:
When users selected one or more subtitle files using "Vali subtiitrifailid" and 
then clicked "Tõlgi eesti keelde", the program incorrectly showed the error:
  "⚠ Viga: Palun valige esmalt kaust!"

This prevented translating individually selected files without requiring a folder.

SOLUTION:
Modified app/gui.py _start_translation() method to support TWO workflows:

1. FOLDER-BASED WORKFLOW (Original - Unchanged)
   ├─ User clicks "Vali kaust" and selects a folder
   ├─ App looks for .en.srt files in that folder
   ├─ Translates all found .en.srt files
   └─ Saved translations: movie.en.srt → movie.et.srt (same folder)

2. INDIVIDUAL FILE SELECTION WORKFLOW (New - Now Working)
   ├─ User clicks "Vali subtiitrifailid" and selects file(s)
   ├─ Folder selection NOT required for this workflow
   ├─ Translates ONLY the selected files
   └─ Saved translations: file.en.srt → file.et.srt (same folder as source)

CHANGES MADE:
File: app/gui.py
Method: SubtitlesApp._start_translation()

Logic Flow (lines 425-500):
1. Check API key (required for both workflows)
   ├─ If missing: show error "Palun sisestage OpenAI API võti!"
   └─ Continue only if API key present

2. Determine which files to translate
   ├─ if self.selected_subtitle_files:  # Individual file workflow
   │  └─ Use selected files directly (folder NOT required)
   └─ else:  # Folder-based workflow
      ├─ Check if folder selected
      ├─ Check if folder exists
      └─ Look for .en.srt files using glob pattern

3. Remaining workflow (unchanged for both)
   ├─ Get selected model from dropdown
   ├─ Map display name to API model ID
   ├─ Initialize TranslationWorker
   ├─ Set up UI state (disable buttons, enable progress)
   ├─ Log model and file count
   └─ Start async translation

KEY FEATURES:
✓ Individual files can be translated without folder selection
✓ Folder-based workflow still works exactly as before
✓ Folder NOT required when individual files are selected
✓ Model selection works for both workflows
✓ Output files saved to source file's directory
✓ Error messages are clear and workflow-specific
✓ No changes to translation logic, SRT parsing, or file I/O

ERROR MESSAGES:
1. No API key (both workflows):
   "⚠ Viga: Palun sisestage OpenAI API võti!"

2. No files selected AND no folder (only in folder workflow):
   "⚠ Viga: Valige kaust VÕI valitud subtiitrifailid!"

3. Selected folder doesn't exist:
   "⚠ Viga: Kausta ei eksisteeri: {folder_path}"

4. No .en.srt files found in folder:
   "ℹ Informatsioon: Kaustast ei leitud .en.srt faile: {folder_path}"

PATH HANDLING:
- Individual file paths stored as strings: self.selected_subtitle_files
- Converted to Path objects for translation: [Path(f) for f in ...]
- Works seamlessly with existing _translate_next_file() method
- Folder .en.srt files already return Path objects from glob()

COMPATIBILITY:
✓ Backward compatible with folder-based workflow
✓ No changes to translation quality or prompt
✓ No changes to MKV processing workflow
✓ No changes to API key handling
✓ No changes to file deletion safety
✓ Model selection (GPT-4.1 / GPT-4.1 mini) works for both
✓ Token usage tracking works for both
✓ Progress logging works for both
✓ Cancellation works for both

TESTING:
✓ Syntax check passed (app/gui.py)
✓ Application startup verified
✓ Workflow logic verified (test_translation_workflows.py)
✓ Both folder and individual file workflows tested
✓ Error cases verified
✓ Path handling verified
✓ Model selection verified
✓ UI state management verified

USAGE EXAMPLES:

Example 1: Folder-based (original workflow)
  1. Click "Vali kaust" → select C:\movies\
  2. Click "Tõlgi eesti keelde"
  3. App finds all .en.srt files in folder
  4. Translates each file
  5. Results: movie1.et.srt, movie2.et.srt in C:\movies\

Example 2: Individual files (new workflow)
  1. Click "Vali subtiitrifailid" → select movie1.srt, movie2.srt
  2. Click "Tõlgi eesti keelde"
  3. App translates ONLY selected files
  4. Folder NOT required
  5. Results: movie1.et.srt, movie2.et.srt in their source directories
