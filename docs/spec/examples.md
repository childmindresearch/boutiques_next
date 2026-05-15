# Examples

Three worked descriptors at increasing complexity. For real-world
descriptors see the [niwrap](https://github.com/styx-api/niwrap/tree/main/src/niwrap)
collection of neuroimaging tool wrappers.

## Basic tool

A converter with one file input, one path output, a numeric flag, and a
boolean flag:

```json
{
  "schema-version": "0.5+styx",
  "name": "image_converter",
  "description": "Convert between image formats with optional compression.",
  "tool-version": "1.0.0",
  "author": "Example author",
  "url": "https://example.org/tool",
  "command-line": "convert_image [INPUT] [OUTPUT] [COMPRESSION] [VERBOSE]",
  "inputs": [
    {
      "id": "input_file",
      "name": "Input image",
      "description": "The input image file to convert.",
      "type": "File",
      "value-key": "[INPUT]",
      "optional": false
    },
    {
      "id": "output_file",
      "name": "Output image",
      "description": "The output image file path.",
      "type": "String",
      "value-key": "[OUTPUT]",
      "optional": false
    },
    {
      "id": "compression_level",
      "name": "Compression level",
      "description": "Level of compression (0-9).",
      "type": "Number",
      "integer": true,
      "minimum": 0,
      "maximum": 9,
      "command-line-flag": "-c",
      "value-key": "[COMPRESSION]",
      "optional": true
    },
    {
      "id": "verbose",
      "name": "Verbose output",
      "description": "Enable verbose logging.",
      "type": "Flag",
      "command-line-flag": "-v",
      "value-key": "[VERBOSE]",
      "optional": true
    }
  ],
  "output-files": [
    {
      "id": "converted_image",
      "name": "Converted image",
      "description": "The output converted image.",
      "path-template": "[OUTPUT]",
      "optional": false
    }
  ],
  "container-image": {
    "type": "docker",
    "image": "example/image-converter:1.0.0"
  }
}
```

## Tool with a sub-command union

A segmentation tool with two mutually exclusive algorithms (`atlas`,
`deep`), each with its own parameter set and its own outputs:

```json
{
  "schema-version": "0.5+styx",
  "name": "brain_segmentation",
  "description": "Perform brain segmentation using different algorithms.",
  "tool-version": "2.0.0",
  "command-line": "segment_brain [ALGORITHM] [GLOBAL_OPTIONS]",
  "inputs": [
    {
      "id": "algorithm",
      "name": "Algorithm",
      "description": "Segmentation algorithm to use.",
      "value-key": "[ALGORITHM]",
      "optional": false,
      "type": [
        {
          "id": "atlas",
          "name": "Atlas-based",
          "description": "Atlas-based segmentation.",
          "command-line": "atlas [INPUT] [OUTPUT] [ATLAS_FILE] [ATLAS_OPTIONS]",
          "inputs": [
            { "id": "input",      "name": "Input image",  "type": "File",   "value-key": "[INPUT]",         "optional": false },
            { "id": "output",     "name": "Output dir",   "type": "String", "value-key": "[OUTPUT]",        "optional": false },
            { "id": "atlas_file", "name": "Atlas file",   "type": "File",   "value-key": "[ATLAS_FILE]",    "optional": false },
            {
              "id": "non_linear", "name": "Non-linear registration",
              "type": "Flag", "command-line-flag": "--nonlinear",
              "value-key": "[ATLAS_OPTIONS]", "optional": true
            }
          ],
          "output-files": [
            { "id": "segmentation", "name": "Segmentation", "path-template": "[OUTPUT]/segmentation.nii.gz" },
            { "id": "labels",       "name": "Label map",    "path-template": "[OUTPUT]/labels.csv" }
          ]
        },
        {
          "id": "deep",
          "name": "Deep learning",
          "description": "Deep-learning-based segmentation.",
          "command-line": "deep [INPUT] [OUTPUT] [MODEL] [DEEP_OPTIONS]",
          "inputs": [
            { "id": "input",  "name": "Input image", "type": "File",   "value-key": "[INPUT]",  "optional": false },
            { "id": "output", "name": "Output dir",  "type": "String", "value-key": "[OUTPUT]", "optional": false },
            {
              "id": "model", "name": "Model type",
              "type": "String", "value-key": "[MODEL]",
              "value-choices": ["unet", "segnet", "densenet"], "optional": false
            },
            {
              "id": "batch_size", "name": "Batch size",
              "type": "Number", "integer": true, "minimum": 1, "maximum": 64,
              "command-line-flag": "--batch", "value-key": "[DEEP_OPTIONS]",
              "optional": true
            },
            {
              "id": "device", "name": "Computing device",
              "type": "String", "command-line-flag": "--device",
              "value-key": "[DEEP_OPTIONS]",
              "value-choices": ["cpu", "cuda"], "optional": true
            }
          ],
          "output-files": [
            { "id": "segmentation",      "name": "Segmentation",      "path-template": "[OUTPUT]/segmentation.nii.gz" },
            { "id": "probability_maps",  "name": "Probability maps",  "path-template": "[OUTPUT]/probabilities.nii.gz" },
            { "id": "metrics",           "name": "Performance metrics", "path-template": "[OUTPUT]/metrics.json" }
          ]
        }
      ]
    },
    {
      "id": "threads", "name": "Number of threads",
      "type": "Number", "integer": true, "minimum": 1,
      "command-line-flag": "--threads", "value-key": "[GLOBAL_OPTIONS]",
      "optional": true
    },
    {
      "id": "verbose", "name": "Verbose output",
      "type": "Flag", "command-line-flag": "--verbose",
      "value-key": "[GLOBAL_OPTIONS]", "optional": true
    }
  ]
}
```

Example invocation selecting the deep algorithm:

```json
{
  "algorithm": {
    "id": "deep",
    "input": "/data/brain.nii",
    "output": "/results",
    "model": "unet",
    "batch_size": 8
  },
  "threads": 4
}
```

## Tool with a repeatable sub-command

A pipeline tool where a `--op X PARAMS` block can repeat:

```json
{
  "schema-version": "0.5+styx",
  "name": "image_processor",
  "description": "Apply multiple image processing operations sequentially.",
  "tool-version": "1.0.0",
  "command-line": "process_image [INPUT] [OUTPUT] [OPERATIONS]",
  "inputs": [
    { "id": "input_file",  "name": "Input image",  "type": "File",   "value-key": "[INPUT]",  "optional": false },
    { "id": "output_file", "name": "Output image", "type": "String", "value-key": "[OUTPUT]", "optional": false },
    {
      "id": "operations",
      "name": "Processing operations",
      "description": "Operations to apply (in order).",
      "value-key": "[OPERATIONS]",
      "list": true,
      "optional": true,
      "type": {
        "id": "operation",
        "command-line": "--op [OPERATION] [PARAMS]",
        "inputs": [
          {
            "id": "operation_type", "name": "Operation type",
            "type": "String", "value-key": "[OPERATION]",
            "value-choices": ["blur", "sharpen", "resize", "rotate", "contrast"],
            "optional": false
          },
          {
            "id": "parameters", "name": "Operation parameters",
            "type": "Number", "list": true, "list-separator": ",",
            "value-key": "[PARAMS]", "optional": false
          }
        ]
      }
    }
  ],
  "output-files": [
    { "id": "processed_image", "name": "Processed image", "path-template": "[OUTPUT]" }
  ]
}
```

With two operations in the invocation, the resolved command-line looks
like:

```
process_image input.jpg output.jpg --op blur 3,3 --op rotate 90
```

## Real-world catalogue

For hundreds of production descriptors covering tools from AFNI, ANTs,
FSL, FreeSurfer, MRtrix, and others, see the
[niwrap](https://github.com/styx-api/niwrap/tree/main/src/niwrap)
collection.
