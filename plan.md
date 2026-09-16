# MicroDrama Studio — AI Coding Plan
## Reusable 10-Minute AI Micro-Drama Production Pipeline

**Version:** 0.1  
**Primary UI:** Streamlit  
**GPU execution:** Modal  
**Video generation:** LTX (initially LTX-2.x / current deployed LTX version)  
**Image generation:** FLUX and/or Qwen Image Edit  
**Goal:** Build a reusable production system where an idea can be transformed into a coherent ~10-minute micro-drama through structured story, character, location, scene, shot, image, video, review, and final-render stages.

---

# 1. Product Vision

Do NOT build an app specifically for one movie.

Build a reusable **MicroDrama Studio**.

The first project may be:

> **After Closing** — horror micro-drama about Lucy, David, and a child trapped in a shopping mall after closing, forced to complete games, and ultimately transformed into mannequins despite completing every game.

The same application must later support:

- Horror
- Thriller
- Mystery
- Romance
- Sci-fi
- Comedy
- Drama
- Fantasy
- Other short-form cinematic stories

The core abstraction is:

```text
Idea
  ↓
Story
  ↓
Production Bible
  ↓
Characters
  ↓
Locations
  ↓
Visual Style
  ↓
Scenes
  ↓
Shots
  ↓
Reference Images / Keyframes
  ↓
Video Generation
  ↓
Review / Regeneration
  ↓
Assembly
  ↓
Final Micro-Drama
```

---

# 2. Core Architectural Principle

Streamlit is the **UI/orchestration layer**.

Modal is the **GPU execution layer**.

Do not run LTX generation directly inside Streamlit.

Preferred architecture:

```text
Browser
  ↓
Streamlit
  ↓
Application / API layer
  ↓
Database
  ↓
Generation Job
  ↓
Modal GPU Worker
  ↓
LTX / Image Model
  ↓
Object Storage
  ↓
Asset Metadata in Database
  ↓
Streamlit Review UI
```

Generation must be asynchronous.

Never make the Streamlit request wait synchronously for a long GPU job.

---

# 3. V1 Scope

V1 must support the complete path for one 10-minute film:

1. Create project
2. Enter core idea
3. Generate structured story
4. Edit/approve story
5. Generate character definitions
6. Generate character reference images
7. Approve character references
8. Generate location definitions
9. Generate location reference images
10. Define visual style
11. Generate scenes
12. Generate shots for each scene
13. Generate image/keyframe prompts
14. Generate keyframes
15. Approve keyframes
16. Generate LTX video clips
17. Review clips
18. Regenerate rejected clips
19. Assemble approved clips
20. Export final video

V1 does NOT need a sophisticated browser-based NLE.

Basic sequential assembly is enough.

---

# 4. Suggested Repository

```text
microdrama-studio/
│
├── app.py
├── requirements.txt
├── .env.example
├── README.md
│
├── pages/
│   ├── dashboard.py
│   ├── story.py
│   ├── characters.py
│   ├── locations.py
│   ├── style.py
│   ├── scenes.py
│   ├── shots.py
│   ├── images.py
│   ├── videos.py
│   ├── review.py
│   ├── editor.py
│   └── final.py
│
├── core/
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── enums.py
│   ├── project_service.py
│   ├── asset_service.py
│   ├── job_service.py
│   └── validation.py
│
├── ai/
│   ├── llm_client.py
│   ├── story_engine.py
│   ├── character_engine.py
│   ├── location_engine.py
│   ├── scene_engine.py
│   ├── shot_engine.py
│   ├── image_prompt_engine.py
│   ├── ltx_prompt_engine.py
│   └── continuity_engine.py
│
├── providers/
│   ├── image/
│   │   ├── base.py
│   │   ├── flux.py
│   │   └── qwen.py
│   │
│   └── video/
│       ├── base.py
│       └── ltx.py
│
├── workers/
│   ├── job_queue.py
│   └── job_runner.py
│
├── modal/
│   ├── image_worker.py
│   ├── ltx_worker.py
│   └── render_worker.py
│
├── storage/
│   ├── object_store.py
│   └── paths.py
│
├── prompts/
│   ├── story/
│   ├── characters/
│   ├── locations/
│   ├── scenes/
│   ├── shots/
│   ├── image/
│   └── ltx/
│
├── schemas/
│   ├── project.py
│   ├── character.py
│   ├── location.py
│   ├── scene.py
│   ├── shot.py
│   ├── asset.py
│   └── job.py
│
└── tests/
```

The exact structure can evolve, but responsibilities must remain separated.

---

# 5. Application Navigation

Use Streamlit multipage navigation.

Sidebar:

```text
MICRODRAMA STUDIO

PROJECT
  Dashboard

PRODUCTION
  01 Story
  02 Characters
  03 Locations
  04 Visual Style
  05 Scenes
  06 Shots
  07 Images
  08 Videos
  09 Review
  10 Final

SYSTEM
  Asset Library
  Jobs
  Settings
```

The UI should always show the current project.

---

# 6. Project Lifecycle

Each project has a production status:

```text
IDEA
STORY_DRAFT
STORY_APPROVED
CHARACTERS_READY
LOCATIONS_READY
STYLE_READY
SCENES_READY
SHOTS_READY
KEYFRAMES_READY
VIDEOS_IN_PROGRESS
VIDEOS_READY
EDIT_READY
FINAL
```

Do not hard-code the workflow so tightly that future projects cannot skip or repeat stages.

A user should be able to regenerate a scene without recreating the entire project.

---

# 7. Project Data Model

Minimum fields:

```python
Project:
    id
    title
    logline
    genre
    target_duration_seconds
    language
    aspect_ratio
    status
    created_at
    updated_at
```

Additional project-level settings:

```text
visual_style_id
image_model
video_model
default_video_duration
default_resolution
default_fps
```

---

# 8. Story Engine

Input:

```text
Core idea
Genre
Target duration
Optional references
Optional user instructions
```

Output MUST be structured data, not only prose.

Example:

```json
{
  "logline": "...",
  "theme": "...",
  "tone": "...",
  "premise": "...",
  "synopsis": "...",
  "story_rules": [],
  "characters": [],
  "locations": [],
  "acts": [],
  "scenes": [],
  "ending": "...",
  "clues": [],
  "continuity_rules": []
}
```

The AI must optimize for a ~10-minute film.

Avoid generating an unnecessarily large feature-film screenplay.

---

# 9. Character Engine

For every important character create a structured Character object.

Minimum:

```text
id
project_id
name
age
role
gender
appearance
hair
face
body
skin
clothing
accessories
personality
behavior
voice_description
character_arc
continuity_constraints
status
```

Also store:

```text
master_reference_asset_id
reference_assets[]
identity_prompt
negative_constraints
```

---

# 10. Character Reference Workflow

For each important character:

```text
Character definition
      ↓
Generate reference prompt
      ↓
Image model
      ↓
Reference images
      ↓
User selects approved image
      ↓
master_reference_asset_id
```

The approved master reference must be reusable across all shots.

Do NOT regenerate the character identity from scratch for every shot.

---

# 11. Location Engine

Locations are first-class assets.

Example:

```text
Mall
Fashion Store
Security Room
Children's Store
Food Court
Main Entrance
Final Store
```

Location schema:

```text
id
project_id
name
description
architecture
materials
lighting
time_of_day
visual_identity
continuity_constraints
master_reference_asset_id
reference_assets[]
```

The same location should maintain visual continuity across scenes.

---

# 12. Visual Style

Project-level visual style:

```text
cinematic_realism
camera_language
lens_preferences
lighting_language
color_progression
contrast
depth_of_field
film_grain
production_design
visual_motifs
```

Style must be inherited by scenes and shots unless explicitly overridden.

Example for After Closing:

```text
Beginning:
warm commercial mall lighting

Middle:
cold fluorescent lighting

Late:
unnatural/surreal lighting

Ending:
clean morning daylight + disturbing stillness
```

---

# 13. Scene Engine

Each scene:

```text
id
project_id
scene_number
title
summary
purpose
duration_seconds
location_id
time_of_day
characters[]
emotional_state
story_beat
dialogue
sound_design
visual_direction
continuity_notes
status
```

Scene generation must consider the total project duration.

The system should warn if scene durations exceed the target runtime.

---

# 14. Shot Engine

Shots are the smallest major production unit.

Shot schema:

```text
id
scene_id
shot_number
duration_seconds

shot_type
camera_angle
camera_movement
lens
framing

characters[]
location_id
action
emotion
dialogue
environment

lighting
sound
visual_effects

image_prompt
video_prompt

reference_assets[]
previous_shot_id
continuity_constraints

status
```

Typical shot durations may be 3–10 seconds depending on the scene and model.

Do not assume every LTX generation must equal final edited duration.

---

# 15. Prompt Engine

Prompt generation must be deterministic from structured data.

Do not let the LLM freely invent character appearance in every shot.

Conceptually:

```text
Project Style
+
Location Bible
+
Character Bible
+
Scene Context
+
Shot Action
+
Camera
+
Lighting
+
Audio
+
Continuity
=
Final Prompt
```

---

# 16. LTX Prompt Rules

LTX prompts should describe executable visual information.

Prefer:

```text
Character
Environment
Action
Camera
Lighting
Motion
Audio
```

Use chronological action.

Avoid keyword soup such as:

```text
masterpiece, 8k, cinematic, beautiful, horror,
ultra detailed, best quality...
```

The LTX prompt generator should produce natural-language prompts appropriate for the deployed LTX version.

For single shots, prefer a concise focused paragraph.

For multi-shot workflows, use explicit shot/cut structure only when the selected LTX workflow supports it.

The app must keep the LTX prompt engine versioned because LTX prompting/model behavior can change.

---

# 17. Image Provider Abstraction

Never hard-code FLUX into business logic.

Interface:

```python
class ImageProvider:
    def generate(self, request) -> GenerationResult:
        ...
```

Implement:

```text
FluxProvider
QwenImageProvider
```

Future:

```text
OtherImageProvider
```

The project can select the image provider.

---

# 18. Video Provider Abstraction

Never hard-code LTX into the entire application.

Interface:

```python
class VideoProvider:
    def generate(self, request) -> GenerationResult:
        ...
```

Initial implementation:

```text
LTXProvider
```

Future providers can be added without changing the shot engine.

---

# 19. Generation Request

Every image/video request should have a structured record.

Example:

```text
GenerationRequest:
    id
    project_id
    scene_id
    shot_id
    provider
    model
    prompt
    negative_prompt
    reference_asset_ids
    parameters
    seed
    status
    created_at
```

Store the exact prompt and parameters used.

Reproducibility matters.

---

# 20. Asset Model

Every generated or uploaded media item is an Asset.

```text
Asset:
    id
    project_id
    type
    file_path
    mime_type

    provider
    model

    prompt
    seed
    parameters

    width
    height
    fps
    duration

    parent_asset_id

    created_at
```

Asset types:

```text
CHARACTER_REFERENCE
LOCATION_REFERENCE
STYLE_REFERENCE
KEYFRAME
VIDEO_CLIP
AUDIO
MUSIC
SFX
FINAL_VIDEO
```

---

# 21. Asset Storage

Do NOT store large videos/images directly in the database.

Store them in object storage or an appropriate persistent volume.

Database stores metadata and object-storage path/key.

Suggested logical structure:

```text
projects/{project_id}/
    characters/{character_id}/
    locations/{location_id}/
    scenes/{scene_id}/
    shots/{shot_id}/
    keyframes/
    videos/
    audio/
    final/
```

---

# 22. Job System

All expensive generation is a Job.

Job states:

```text
QUEUED
RUNNING
SUCCEEDED
FAILED
CANCELLED
```

Job schema:

```text
id
project_id
type
provider
payload
status
progress
result_asset_ids
error
created_at
started_at
completed_at
```

Job types:

```text
STORY_GENERATION
CHARACTER_IMAGE
LOCATION_IMAGE
KEYFRAME_IMAGE
VIDEO_GENERATION
VIDEO_ASSEMBLY
```

---

# 23. Modal Architecture

Initial Modal deployment:

```text
Modal App
│
├── LTX Worker
├── Image Worker
└── Render Worker
```

Workers should be independently callable.

Conceptual:

```text
Streamlit
   ↓
submit_generation_job()
   ↓
Modal function
   ↓
GPU
   ↓
write result
   ↓
return job/result metadata
```

Keep model loading warm where economically useful, but do not assume a permanently running GPU.

GPU/resource configuration must be configurable.

---

# 24. LTX Worker

The LTX worker is responsible only for video generation.

Input:

```json
{
  "prompt": "...",
  "reference_assets": [],
  "width": 1920,
  "height": 1080,
  "fps": 24,
  "duration": 6,
  "seed": 12345,
  "workflow_parameters": {}
}
```

Output:

```json
{
  "status": "success",
  "asset_path": "...",
  "metadata": {}
}
```

Do not put story logic inside the LTX worker.

---

# 25. Image Worker

The image worker should support:

```text
Text → Image
Image → Image
Reference-guided generation
Editing
```

Depending on provider capabilities.

The app must know which operations a provider supports.

Example capability flags:

```text
text_to_image
image_to_image
image_edit
multi_reference
```

---

# 26. Batch Generation

Users should eventually be able to select:

```text
Scene 03
☑ Shot 021
☑ Shot 022
☑ Shot 023
☑ Shot 024

[Generate Selected]
```

Jobs should enter a queue.

Do not block the UI.

Display:

```text
Shot 021   ✓
Shot 022   ✓
Shot 023   Generating
Shot 024   Queued
```

---

# 27. Review Workflow

Every generated asset should support:

```text
APPROVE
REJECT
REGENERATE
```

For rejection, capture a reason:

```text
wrong face
wrong clothing
bad motion
bad camera
wrong environment
continuity problem
poor quality
wrong emotion
other
```

This reason can be fed into the regeneration prompt.

---

# 28. Continuity Engine

V1 can be lightweight, but architecture must support automated continuity checks.

Check:

### Character

```text
face
hair
clothing
accessories
age
appearance
```

### Location

```text
architecture
lighting
layout
time
props
```

### Story

```text
character present?
character knows information yet?
object exists?
injury exists?
previous event respected?
```

### Temporal continuity

```text
time of day
weather
costume
physical state
```

Return:

```json
{
  "status": "warning",
  "issues": [
    "Lucy necklace missing",
    "Scene lighting differs from previous shot"
  ]
}
```

Do not automatically reject unless configured.

---

# 29. Prompt Versioning

Every prompt must be versioned.

```text
PromptVersion:
    id
    target_type
    target_id
    version
    prompt
    model
    created_at
```

Never overwrite the only copy of a prompt.

A user should be able to see:

```text
Prompt v1
Prompt v2
Prompt v3
```

and identify which generated asset came from which prompt.

---

# 30. Seed and Parameter Reproducibility

Store:

```text
seed
model
model_version
steps
guidance
resolution
fps
duration
workflow version
```

where supported.

Do not assume all providers expose all parameters.

Use provider-specific parameter dictionaries.

---

# 31. Scene Production UI

Scene page should show:

```text
SCENE 04 — THE CHILD

Duration: 48 sec
Location: Children's Store
Characters: Lucy, David, Emma

Story Purpose:
...

[Edit Scene]
[Generate Shots]
```

Then:

```text
SHOTS

001  ✓ Keyframe ✓ Video
002  ✓ Keyframe ⏳ Video
003  ✓ Keyframe ✓ Video
004  ✗ Keyframe
```

---

# 32. Shot UI

Shot page:

```text
SHOT 017

Duration: 6 sec

Character:
Lucy

Location:
Children's Store

Action:
Lucy slowly approaches the mannequin...

Camera:
Slow dolly backward

Lighting:
Cold fluorescent

Audio:
Distant child's humming

REFERENCE ASSETS
[Lucy master]
[Children's store master]

IMAGE PROMPT
[...........................]

VIDEO PROMPT
[...........................]

[Generate Keyframe]
[Generate Video]
[Regenerate]
```

Show generated image/video directly.

---

# 33. Edit / Assembly V1

V1 does not require a full nonlinear editor.

Provide:

```text
Scene 01
  Shot 001
  Shot 002
  Shot 003

Scene 02
  Shot 004
  Shot 005
```

Allow:

```text
drag/reorder
trim start/end
mute
volume
```

If drag/reorder is too complex for V1, provide numeric ordering.

Use FFmpeg or a dedicated render worker for assembly.

---

# 34. Final Render

Final page:

```text
PROJECT: AFTER CLOSING

Runtime:
09:57

Shots:
67

Approved:
64

Missing:
3

[Render Final]

Output:
after_closing_final.mp4
```

Do not allow final render while required shots are missing unless the user explicitly overrides.

---

# 35. Dashboard

Dashboard should show:

```text
AFTER CLOSING

Genre: Horror
Target: 10:00
Current: 07:42 generated

Progress
██████████████░░░░ 78%

Characters
3 / 3 ✓

Locations
5 / 5 ✓

Scenes
11 / 11 ✓

Keyframes
58 / 67

Videos
41 / 67

Final
Not ready
```

---

# 36. Error Handling

Every generation must handle:

```text
GPU failure
timeout
OOM
provider failure
invalid prompt
missing reference
storage failure
network failure
```

A failed job must remain inspectable.

Allow:

```text
Retry
Cancel
Edit parameters
Regenerate
```

Never lose the original request.

---

# 37. Configuration

Use environment variables/secrets.

Example:

```text
DATABASE_URL=
OBJECT_STORAGE_URL=
OBJECT_STORAGE_BUCKET=

MODAL_APP_NAME=
MODAL_ENVIRONMENT=

LLM_API_KEY=

FLUX_CONFIG=
QWEN_CONFIG=
LTX_CONFIG=
```

Do not hard-code API keys.

Do not commit secrets.

---

# 38. Streamlit State Rules

Use Streamlit session state only for transient UI state.

Do NOT use it as the project's persistent state.

Persistent state belongs in the database.

Examples of session state:

```text
current_project_id
selected_scene_id
selected_shot_id
temporary UI filters
```

---

# 39. AI Output Validation

LLM-generated structured output must be validated before saving.

Use Pydantic or equivalent schema validation.

Example:

```python
story = StorySchema.model_validate(llm_output)
```

If invalid:

```text
LLM output
 ↓
schema validation
 ↓
repair / retry
 ↓
validated object
 ↓
database
```

Never blindly save arbitrary LLM JSON.

---

# 40. Human Approval Gates

Important production stages should require approval.

Default:

```text
Story
   ↓ APPROVE

Characters
   ↓ APPROVE

Locations
   ↓ APPROVE

Style
   ↓ APPROVE

Scenes
   ↓ APPROVE

Shots
   ↓

Keyframes
   ↓ APPROVE

Video
   ↓ APPROVE

Final
```

The user should always remain in control.

---

# 41. After Closing — Seed Project

Use this project as the first end-to-end test.

Characters:

```text
Lucy
David
Emma
```

Core premise:

```text
Lucy attends a party in a shopping mall.
The mall closes at night and traps everyone inside.
Lucy meets David and a mysterious child.
The mall forces them through games.
Lucy successfully completes every game.
She believes she has won.
At morning, she discovers that completing the games was the process that transformed her.
David, Emma and previous victims are also mannequins.
The final announcement says:
"Next player."
```

Important horror rule:

> There is no winning condition. The games are the mall's transformation ritual.
This story is ONLY seed content.

Do not hard-code Lucy, David, Emma, mall, or horror-specific logic into the application.

---

# 42. Development Phases

## PHASE 0 — Architecture

Deliver:

- Repository
- Configuration
- Environment setup
- Database connection
- Basic Streamlit navigation
- Core schemas
- Provider interfaces

Acceptance:

```text
App starts.
Database connects.
Project can be created.
No GPU generation yet.
```

---

## PHASE 1 — Project + Story

Build:

- Project creation
- Story page
- LLM integration
- Structured story generation
- Story editing
- Story approval
- Project status

Acceptance:

```text
User enters idea.
AI generates structured story.
User edits it.
User approves it.
Story persists after refresh.
```

---

## PHASE 2 — Characters + Locations + Style

Build:

- Character generation
- Character editing
- Location generation
- Location editing
- Style definition
- Reference-image generation interface
- Asset persistence

Acceptance:

```text
User can create complete production bible.
Character/location references can be generated and approved.
```

---

## PHASE 3 — Scenes + Shots

Build:

- Scene generation
- Scene editing
- Shot generation
- Shot editing
- Duration calculation
- Story continuity metadata

Acceptance:

```text
Approved story → scenes → shots.
Total estimated runtime is visible.
```

---

## PHASE 4 — Image Generation

Build:

- ImageProvider interface
- FLUX implementation
- Qwen implementation if available
- Modal image worker
- Character reference generation
- Location reference generation
- Keyframe generation
- Asset gallery

Acceptance:

```text
Select character.
Generate image.
Receive job.
Job completes asynchronously.
Image appears in asset library.
User approves one reference.
```

---

## PHASE 5 — LTX Video

Build:

- VideoProvider interface
- LTX provider
- Modal LTX worker
- LTX prompt engine
- Image-to-video workflow
- Text-to-video fallback
- Video asset storage

Acceptance:

```text
Approved keyframe + shot data
→ LTX prompt
→ Modal
→ video
→ asset library
→ review.
```

---

## PHASE 6 — Review + Regeneration

Build:

- Video review
- Approve/reject
- Regeneration reasons
- Prompt revision
- Version history
- Batch generation

Acceptance:

```text
User can reject a clip.
System preserves old clip.
System generates a new version.
Both versions remain traceable.
```

---

## PHASE 7 — Assembly

Build:

- Shot ordering
- Scene ordering
- Basic trim
- Audio tracks
- FFmpeg/render worker
- Final render

Acceptance:

```text
Approved clips
→ ordered timeline
→ render
→ playable final MP4.
```

---

## PHASE 8 — Continuity

Build:

- Character continuity checks
- Location continuity checks
- Prop continuity
- Costume continuity
- Time continuity
- Story-state checks

Acceptance:

```text
Before generation:
system warns about obvious continuity conflicts.
```

---

## PHASE 9 — Production Optimization

Build:

- Batch jobs
- GPU utilization optimization
- caching
- retry policies
- cost tracking
- generation statistics
- queue management

---

## PHASE 10 — Reusable MicroDrama Platform

Build:

- Project templates
- Genre presets
- Style presets
- Reusable characters
- Reusable locations
- Asset library
- Multiple video providers
- Multiple image providers
- Export/import project
- Project duplication

Goal:

```text
New Project
→ choose template
→ enter idea
→ production pipeline
```

---

# 43. What NOT to Build Yet

Do not over-engineer V1 with:

- full Premiere-like editor
- social media publishing
- user billing
- collaboration
- marketplace
- mobile app
- automatic voice acting
- automatic lip sync
- complex music generation
- advanced 3D scene reconstruction

Those can come later.

First prove:

```text
Idea → coherent 10-minute micro-drama.
```

---

# 44. Critical Engineering Rules

1. **No hard-coded movie-specific logic.**
2. **No hard-coded character descriptions inside video workers.**
3. **No synchronous long-running GPU calls from Streamlit.**
4. **No API keys in source code.**
5. **No large media files in the relational database.**
6. **Every generation must have an ID.**
7. **Every generated asset must preserve its prompt and parameters.**
8. **Never overwrite previous generations.**
9. **Use provider abstractions.**
10. **Use validated structured schemas between AI stages.**
11. **Persistent project state belongs in the database.**
12. **Human approval must exist between major stages.**
13. **Continuity is a first-class concern.**
14. **The system must support regeneration without destroying previous work.**
15. **Model versions and prompt versions must be traceable.**

---

# 45. Definition of Done for V1

V1 is complete when a user can:

```text
1. Create "After Closing"

2. Enter:
   "A girl enters a shopping mall..."

3. Generate and approve story.

4. Generate:
   Lucy
   David
   Emma

5. Generate and approve their reference images.

6. Generate and approve mall/location references.

7. Define visual style.

8. Generate 10–12 scenes.

9. Generate shots.

10. Generate keyframes.

11. Approve keyframes.

12. Generate LTX videos through Modal.

13. Review each video.

14. Regenerate failed shots.

15. Preserve all versions.

16. Assemble approved shots.

17. Render:
   after_closing_final.mp4
```

Then create a second project:

```text
New Project
→ completely different genre/story
→ same pipeline
```

without modifying the application code.

That is the actual proof that MicroDrama Studio is reusable.
