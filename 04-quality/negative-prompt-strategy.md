# Negative Prompt Strategy Guide

## Goal
Explain why the default negative prompt exists and when to adjust it.

## Baseline
- lowres: reduces low-resolution blur
- bad anatomy: fixes general deformation
- bad hands: improves hand anatomy
- missing finger / extra digits / fewer digits: corrects finger issues
- text / signature / watermark / username: removes text overlays and marks
- blurry: reduces blur

## When to add terms
- If recurring “logo” or text appears → keep `text, watermark, signature, username`
- If the image shows heavy noise/grain → add `noise, jpeg artifacts` when appropriate
- If the result looks “plastic” → be cautious: too many negatives can strip details

## Rule of thumb
- Start with the baseline.
- Adjust 1–3 terms per iteration.
- Avoid unnecessarily long negative lists.
