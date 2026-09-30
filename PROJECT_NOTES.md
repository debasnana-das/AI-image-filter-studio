# Project Explanation

## Problem statement

Traditional photo filters force users to choose from predefined controls. This project allows users to describe an intended visual change in natural language and uses an AI image-editing model to apply it to the uploaded image.

## Inputs

- Image: PNG/JPG/JPEG/WEBP
- Description: free-form natural-language editing instruction

## Processing pipeline

1. Validate the uploaded image.
2. Read the user's description.
3. Add an instruction layer telling the image model to preserve unrelated details.
4. Send the image + prompt to GPT Image 2 through the Image API edit endpoint.
5. Decode the base64 result.
6. Save and display the edited image.

## Output

- AI-filtered/edited PNG image.
- Downloadable result.
- Local copy in `outputs/`.

## Why this is different from a normal filter app

A traditional filter can implement deterministic operations such as brightness, contrast, Gaussian blur, saturation, or a LUT. This project supports semantic edits such as:

- "Make it look like golden hour."
- "Blur the background but keep me sharp."
- "Remove the person in the background."
- "Give this a cinematic blue-orange grade."
- "Turn the sky into a sunset."

Those requests require an image-generation/editing model rather than only fixed pixel operations.
