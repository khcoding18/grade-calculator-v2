# Grade Calculator

A desktop application for calculating a weighted course grade, built with Python and tkinter.

Developed by Kora Hartman. For questions or concerns, contact hartman.devs@gmail.com.

Developed with the assistance of [Claude](https://claude.ai) by Anthropic.

## Requirements

- Python 3.10 or later (uses `list[str]` type hints)
- No third-party packages — only the Python standard library

## Running the Application

```
python grade_calculator.py
```

## Usage

1. **Welcome tab** — Set the *Weight Possible* field to the total weight of your course (default: 100%).
2. **Category tabs** — Enter a *Weight* and *Grade* for each graded item in the relevant tab. Use the **+ Add New Grade** button to add more rows. The six available categories are:
   - Exam
   - Homework
   - Lab
   - Quiz
   - In-Class Work
   - Miscellaneous
3. **Results tab** — Click **Calculate Grades** to compute your final grade and the contribution from each category.

> If the entered weights do not sum to the Weight Possible value, a warning is shown but the calculation still runs.

## File Format

Grades can be saved and re-opened via **File → Save** and **File → Open**. Files are plain text with one value per line:

```
<weight_possible>
<exam_weights>
<exam_grades>
<homework_weights>
<homework_grades>
<lab_weights>
<lab_grades>
<quiz_weights>
<quiz_grades>
<inclass_weights>
<inclass_grades>
<misc_weights>
<misc_grades>
```

Weight and grade values within a line are comma-separated (e.g. `25, 30, 20`).

## License

This application is provided without any warranty, implied or otherwise.
