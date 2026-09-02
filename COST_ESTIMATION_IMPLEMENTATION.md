# API Cost Estimation Feature - Implementation Summary

## Overview
Added a pre-translation cost estimation feature that calculates approximate translation costs locally without making any API calls. Users can now click "Arvuta hinnaprognoos" button to see estimated costs before starting translation.

---

## Files Changed

### 1. **app/cost_estimator.py** (NEW)
- New module for cost estimation logic
- Contains `CostEstimator` class with methods for:
  - Counting tokens in SRT files locally
  - Estimating output tokens using configurable ratios
  - Calculating total API costs with prompt overhead
  - Formatting results for display

### 2. **app/gui.py** (MODIFIED)
- Added import: `from app.cost_estimator import CostEstimator`
- In `__init__`: Added `self.cost_estimator = CostEstimator()`
- In `_create_widgets()`: 
  - Added "Arvuta hinnaprognoos" button in button frame
  - Updated button frame column configuration from 3 to 4 columns
- Added new methods:
  - `_estimate_translation_cost()`: Handler for estimate button click
  - `_update_estimate_button_state()`: Enable/disable button based on file selection
- Modified methods:
  - `_update_workflow_display()`: Calls `_update_estimate_button_state()`
  - `_select_subtitle_files()`: Calls `_update_estimate_button_state()`
  - `_select_folder()`: Calls `_update_estimate_button_state()`

---

## Key Features

### 1. **Tokenizer Used**
- **tiktoken** (OpenAI's official tokenizer)
- Package: `tiktoken`
- Encoding: `cl100k_base` (same as GPT models)
- Falls back to character-based estimate (÷4) if tiktoken unavailable

### 2. **Configuration Parameters**
Located in `app/cost_estimator.py`:

```python
TOKEN_RATIO_CONFIG = {
    "low": 0.65,          # Conservative output estimate
    "expected": 0.75,     # Expected output estimate
    "high": 0.90,         # Liberal output estimate
}

PROMPT_OVERHEAD_TOKENS_PER_BATCH = 500
```

### 3. **Model Pricing (From GUI Model Configuration)**
Uses existing `MODEL_CONFIG` in `app/gui.py`:

```
GPT-4.1 mini:    $0.40 input, $1.60 output per 1M tokens
GPT-4.1:         $2.00 input, $8.00 output per 1M tokens
GPT-5.6 Terra:   $2.50 input, $15.00 output per 1M tokens
```

### 4. **Prompt Overhead Calculation**
- Each batch includes system message and instructions
- Estimated at 500 tokens per batch
- Number of batches calculated from: `(entry_count + batch_size - 1) // batch_size`
- Total input tokens = subtitle text tokens + (batches × 500)

### 5. **Cost Formula**
```
input_cost = (input_tokens / 1,000,000) × input_price_per_1m

output_cost_low = (output_tokens_low / 1,000,000) × output_price_per_1m
output_cost_expected = (output_tokens_expected / 1,000,000) × output_price_per_1m
output_cost_high = (output_tokens_high / 1,000,000) × output_price_per_1m

total_cost_low = input_cost + output_cost_low
total_cost_expected = input_cost + output_cost_expected
total_cost_high = input_cost + output_cost_high
```

### 6. **Display Format (Estonian)**
```
HINNAPROGNOOS
============================================================
Mudel: GPT-4.1 — hea | $1 suhteline hinnatase
Faile: 1
Subtiitriplokke: 3

Hinnanguline sisend:
  521 tokenit
  (teksti: 21 + pea: 500)

Hinnanguline väljund:
  madal: 13 tokenit
  umbes: 15 tokenit
  kõrge: 18 tokenit

Prognoositav API kulu:
  umbes $0.0012
  tõenäoline vahemik: $0.0011–$0.0012

NB! Tegemist on hinnanguga.
Tegelik kulu kuvatakse pärast tõlkimist tegelike tokenite põhjal.
============================================================
```

### 7. **Multiple Files Support**
- Combines token usage from all selected files
- Shows total files and total entries
- Calculates total estimated cost
- Optionally shows average cost per file (for 2+ files)

### 8. **Button Behavior**
- **Initially disabled** when no files selected
- **Enabled** when files are selected for translation
- Works independently - doesn't start translation
- Works without API key
- Automatically updates state when:
  - Workflow mode changes
  - Files are selected/deselected
  - Folder is selected/changed

---

## Tests Created

### 1. **test_cost_estimator.py**
Tests the cost estimator module directly:
- ✓ Single file token counting
- ✓ Cost estimates for different models
- ✓ Formatted output generation
- ✓ Multiple file support
- ✓ Empty file list handling
- ✓ Cross-model cost comparison

### 2. **test_gui_cost_integration.py**
Tests GUI integration:
- ✓ Button exists and has correct text
- ✓ Button is disabled initially
- ✓ Button state updates when files selected
- ✓ Cost estimation produces output in log
- ✓ Works without API key
- ✓ Works with multiple models
- ✓ CostEstimator properly initialized

### 3. **test_no_api_calls.py**
Verifies no external API calls:
- ✓ OpenAI module not required
- ✓ No OpenAI client created
- ✓ Tokenizer operations are local
- ✓ No API keys stored or used
- ✓ Token counting is deterministic and local

---

## Test Results Summary

All tests pass successfully:

```
test_cost_estimator.py ...................... PASSED
test_gui_cost_integration.py ................ PASSED
test_no_api_calls.py ........................ PASSED
```

### Sample Output from test_cost_estimator.py:
```
Files: 1
Total entries: 3
Text tokens: 21
Estimated batches: 1
Input tokens (with overhead): 521

Output tokens estimates:
  Low:  13
  Exp:  15
  High: 18

Estimated costs:
  Low:      $0.0011
  Expected: $0.0012
  High:     $0.0012
```

---

## Requirements Met

✅ **1. ADD A BUTTON**
- Button "Arvuta hinnaprognoos" added to GUI
- Does NOT call OpenAI API
- Calculates estimate locally from selected files

✅ **2. COUNT SOURCE TEXT**
- Parses SRT files correctly
- Includes only subtitle dialogue text
- Excludes timestamps and sequence numbers
- Counts tokens using tiktoken

✅ **3. ESTIMATE OUTPUT TOKENS**
- Uses configurable ratios for output estimation
- Default for Estonian: 0.75 expected ratio
- Range: 0.65 (low) to 0.90 (high)

✅ **4. MODEL PRICING**
- Uses existing central MODEL_CONFIG
- Actual API prices maintained
- No duplication of pricing data

✅ **5. INCLUDE PROMPT OVERHEAD**
- Adds 500 tokens per batch for overhead
- Calculated from actual batch counts
- Used in input token estimation

✅ **6. COST FORMULA**
- Correctly implements all three cost estimates
- Accounts for input and output separately
- Provides low, expected, and high ranges

✅ **7. DISPLAY RESULT**
- Shows results in activity log
- Estonian language
- Clear, readable format
- Includes disclaimer about estimates

✅ **8. AUTOMATIC UPDATE**
- Button state updates when files/model changes
- Explicit button (not continuous updating)
- Prevents complex UI behavior

✅ **9. MULTIPLE FILES**
- Combines tokens from multiple files
- Shows total files and entries
- Shows average cost per file (when applicable)

✅ **10. NO API KEY REQUIRED**
- Works without OpenAI API key
- Completely local calculations
- No external API calls

✅ **11. DO NOT CHANGE TRANSLATION LOGIC**
- Translation behavior unchanged
- No modifications to:
  - Translation prompts
  - SRT parsing for translation
  - Model selection
  - API calls
  - Retry logic
  - Post-translation cost display

✅ **12. TESTING**
- No paid API calls during testing
- Used existing sample .srt files
- Verified all core functionality
- Verified no API calls made

---

## Installation & Dependencies

### Required Change
Install tiktoken for token counting:
```bash
pip install tiktoken
```

### Already Available
- app/gui.py (modified)
- Tkinter (already used by project)
- Model configuration (already exists)
- SRT parsing (already implemented)

---

## Usage

1. **Select files** (via "Vali subtiitrifailid" or folder)
2. **Select model** from dropdown
3. **Click "Arvuta hinnaprognoos"** button
4. **View estimate** in the activity log
5. **Decision**: Proceed with "Tõlgi eesti keelde" or modify selection

---

## No Breaking Changes

- All existing functionality preserved
- New feature is completely optional
- Users can ignore the estimate button if desired
- Existing translation workflow unchanged
- Post-translation cost reporting still works
