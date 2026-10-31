---
template_type: docs
template_id: readme
template_version: 1
requires_slots:
  - TITLE
  - OWNER
  - DATE
  - PURPOSE
  - STRUCTURE_POINTER
  - ENTRY_POINT
  - CONSTRAINTS
  - CANONICAL_POINTER
slot_notes:
  TITLE: the folder or system this README describes, as a heading
  OWNER: the resident who owns this README, as Role (Person) or Person
  DATE: the date written, YYYY-MM-DD
  PURPOSE: what the folder is for, in two or three sentences
  STRUCTURE_POINTER: what lives where, as a short list or table of paths
  ENTRY_POINT: the first command or file a reader opens
  CONSTRAINTS: what may not be put here, and what is read-only
  CANONICAL_POINTER: the authoritative record this README points to (a spec, registry or map); a README is a pointer, not the record
---
# {{TITLE}}

Owner: {{OWNER}}. Written {{DATE}}. Convention: STELA (`Projects/STELA`).

## Purpose
{{PURPOSE}}

## Structure
{{STRUCTURE_POINTER}}

## Entry Point
{{ENTRY_POINT}}

## Constraints
{{CONSTRAINTS}}

## Canonical Pointer
{{CANONICAL_POINTER}}
