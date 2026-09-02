# Estonian Subtitle Translator

A Windows desktop application for translating subtitle files into Estonian using AI.

The project was created as a practical automation tool for processing and translating subtitles with as little manual work as possible.

## Features

- Translate existing `.srt` subtitle files into Estonian
- Process folders containing `.mkv` video files
- Extract English subtitles from MKV files and translate them into Estonian
- Automatic subtitle language detection
- Translation cost estimation before sending data to the API
- Translation progress tracking
- Resume interrupted translations from checkpoints
- Multiple AI model selection
- Retry logic and error handling
- Activity logging
- Responsive Windows GUI
- Source subtitle protection and backup handling

## Two workflows

### 1. Translate existing subtitle files

Select one or more `.srt` files and translate them directly into Estonian.

No video file or folder is required.

### 2. Process MKV files

Select a folder containing `.mkv` files.

The application can:

1. extract English subtitles from the MKV file
2. create an `.en.srt` subtitle file
3. translate the subtitles into Estonian

MKV processing uses MKVToolNix.

## Language detection

Subtitle language is detected locally before translation.

The application can warn the user if:

- the subtitle already appears to be Estonian
- the subtitle is not English
- files with different languages are selected

Language detection does not require an API call.

## Cost estimation

Before starting a translation, the application can estimate the approximate API cost.

The estimate is calculated locally from the subtitle text and selected AI model, so checking the estimated price does not itself make an API request.

## Resume interrupted translations

Long translations can be resumed after interruption.

The application stores translation progress in checkpoint files and can continue from the last successfully completed batch instead of starting again from the beginning.

## Security

API keys are not included in this repository.

The API key is supplied by the user at runtime and should never be committed to source control.

Local virtual environments, cache files, `.env` files and bundled third-party binaries are excluded through `.gitignore`.

## Technology

- Python
- Tkinter
- OpenAI API
- SRT subtitle processing
- MKVToolNix integration
- Token-based API cost estimation
- Automated tests

## Project structure

`app/` contains the main application modules, including:

- GUI
- translation logic
- subtitle processing
- MKV processing
- language detection
- cost estimation
- backup and checkpoint management

The repository also contains automated tests and implementation documentation.

## Status

This is an actively developed personal automation project.

It was built to solve a real-world problem: making foreign-language video content easier to watch with Estonian subtitles while minimizing repetitive manual work.

## Author

**Janek Jüssi**

IT Consultant & Entrepreneur  
Infrastructure, Cybersecurity, Backup & Automation

[LinkedIn](https://www.linkedin.com/in/janek-j%C3%BCssi-612595aa/)