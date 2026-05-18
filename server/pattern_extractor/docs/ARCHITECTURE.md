# Radiation Pattern Extraction — Architecture

## Overview

The system reads radiation pattern images from antenna datasheets,
extracts the 2D polar pattern shape, calibrates it against known dB
scale anchors, and outputs structured JSON data (angle vs magnitude).

Each image is processed independently. All manufacturer-specific
parameters are centralized in `config/manufacturer_config.py`.
Adding a new manufacturer requires only changes to that file.

---

## Data Flow


```mermaid
flowchart TD
    subgraph INPUTS
        CFG["manufacturer_config.py
        rgb_range
        angle_offset_deg
        db_scale: min_db, max_db
        circle_color_range
        max_ring_radius_px"]

        QUEUE["PROCESSING_QUEUE
        - List of tuples:
        (image_path, manufacturer_key)"]
    end
    subgraph "STEP 1: Load"
        LOAD["[1] image_loader
        - Load PNG from disk
        - Convert BGR -> RGB
        - Return HxW x3 numpy array"]
    end
    subgraph "STEP 2: Pattern mask"
        MASK["[2] pattern_mask
        - Apply rgb_range filter
        - Output binary mask:
          0 = pattern pixel
          255 = background"]
    end
    subgraph "STEP 3: Circle detection"
        RINGMASK["[3a] ring_mask_extractor
        - Input: img_rgb, circle_color_range
        - Apply color range filter
        - Return ring_mask (HxW uint8)"]

        CENTER["[3b] center_detector
        - Input: ring_mask
        - Run Hough Circle Transform
        - Cluster detected centers
        - Return: center (cx, cy)"]

        OUTER["[3c] outer_ring_detector
        - Input: ring_mask, center, max_ring_radius_px
        - Scan radii outer -> inner
        - Validate by pixel density
        - Return: outer_radius_px"]

        DBG_3A["[debug] ring_mask.png
        ring_mask visualized"]

        DBG_3B["[debug] center_overlay.png
        img_rgb + detected center"]

        DBG_3C["[debug] outer_ring_overlay.png
        img_rgb + center + outer circle"]
    end

    subgraph "STEP 4: Polar sampling"
        POLAR["[4] polar_sampler
        - For each angle 0..359deg:
          Cast ray from center
          Find outermost coherent
          pattern pixel (gap filter)
        - Map distance -> dB
        - Linear interpolation
        - Return: [{angle_deg, magnitude_db}]"]
    end
    subgraph "STEP 5: Outputs"
        VIZ["[5] visualizer
        - Draw mask (B&W)
        - Mark center (red crosshair), and outer radius
        - Save annotated PNG"]

        WRITER["[6] result_writer
        - Build JSON payload
        - Write to output/json/"]
    end

    subgraph OUTPUT_PATH
        OUT_IMG["output/images/*.png
        Annotated pattern image"]
        OUT_JSON["output/json/*.json
        angle_deg vs magnitude_db"]
    end
    %% FLOW
    CFG -->|"manufacturer key + params"| LOAD
    QUEUE -->|"(image_path, manufacturer)"| LOAD
    LOAD -->|"img_rgb"| MASK
    LOAD -->|"img_rgb"| RINGMASK
    CFG -->|"rgb_range"| MASK
    CFG -->|"circle_color_range"| RINGMASK
    CFG -->|"max_ring_radius_px"| OUTER
    RINGMASK -->|"ring_mask"| CENTER
    RINGMASK -->|"ring_mask"| OUTER
    CENTER -->|"center (cx, cy)"| OUTER
    MASK -->|"binary mask"| POLAR
    CENTER -->|"center (cx, cy)"| POLAR
    OUTER -->|"outer_radius_px"| POLAR
    CFG -->|"min_db, max_db, angle_offset_deg"| POLAR
    MASK -->|"binary mask"| VIZ
    CENTER -->|"center (cx, cy)"| VIZ
    OUTER -->|"outer_radius_px"| VIZ
    POLAR -->|"samples[]"| WRITER
    CENTER -->|"center (cx, cy)"| WRITER
    OUTER -->|"outer_radius_px"| WRITER
    VIZ --> OUT_IMG
    WRITER --> OUT_JSON

    RINGMASK -.->|"if DEBUG_STEPS"| DBG_3A
    CENTER -.->|"if DEBUG_STEPS"| DBG_3B
    OUTER -.->|"if DEBUG_STEPS"| DBG_3C
```
---

## Key Design Decisions

`manufacturer_config.py` is the only place that changes when adding a
manufacturer.

The dB scale is purely linear between two anchors:
- `distance = 0` maps to `min_db`
- `distance = outer_radius_px` maps to `max_db`


**`outer_radius_px` comes from circle detection, not from the pattern.**
The pattern shape rarely reaches the outermost ring. Using the pattern
extent to estimate scale would produce systematic dB errors. The
concentric rings in the image are the calibration ground truth.


---

## Directory Structure
```
pattern_extractor/
    main.py
    config/
        __init__.py
        manufacturer_config.py
    modules/
        __init__.py
        image_loader.py
        pattern_mask.py
        ring_mask_extractor.py
        center_detector.py
        outer_ring_detector.py
        polar_sampler.py
        visualizer.py
        result_writer.py
    datasheets/
        taoglas-1.png
        taoglas-2.png
        rf-elements-1.png
        molex-1.png
        alpha-wireless-1.png
        quectel-1.png
    output/
        images/
        json/
        debug/
            ring_mask/
            center_overlay/
            outer_ring_overlay/
    docs/
        ARCHITECTURE.md
        MODULES_DETAIL.md
```