# FreeCAD Robust MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI Version](https://img.shields.io/pypi/v/freecad-robust-mcp)](https://pypi.org/project/freecad-robust-mcp/)
[![Python Versions](https://img.shields.io/pypi/pyversions/freecad-robust-mcp)](https://pypi.org/project/freecad-robust-mcp/)
[![Docker Image Version](https://img.shields.io/docker/v/spkane/freecad-robust-mcp?sort=semver&label=docker)](https://hub.docker.com/r/spkane/freecad-robust-mcp)
[![Documentation](https://img.shields.io/badge/docs-latest-blue.svg)](https://spkane.github.io/freecad-addon-robust-mcp-server/)

[![CI Tests](https://github.com/spkane/freecad-addon-robust-mcp-server/actions/workflows/test.yaml/badge.svg)](https://github.com/spkane/freecad-addon-robust-mcp-server/actions/workflows/test.yaml)
[![Docker Build](https://github.com/spkane/freecad-addon-robust-mcp-server/actions/workflows/docker.yaml/badge.svg)](https://github.com/spkane/freecad-addon-robust-mcp-server/actions/workflows/docker.yaml)
[![Pre-commit](https://github.com/spkane/freecad-addon-robust-mcp-server/actions/workflows/pre-commit.yaml/badge.svg)](https://github.com/spkane/freecad-addon-robust-mcp-server/actions/workflows/pre-commit.yaml)
[![CodeQL](https://github.com/spkane/freecad-addon-robust-mcp-server/actions/workflows/codeql.yaml/badge.svg)](https://github.com/spkane/freecad-addon-robust-mcp-server/actions/workflows/codeql.yaml)

An [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) server that enables integration between AI assistants (Claude, GPT, and other MCP-compatible tools) and [FreeCAD](https://www.freecadweb.org/), allowing AI-assisted development and debugging of 3D models, macros, and workbenches.

## Table of Contents

<!--TOC-->


- [FreeCAD Robust MCP Server](#freecad-robust-mcp-server)

  - [Table of Contents](#table-of-contents)

  - [Features](#features)

  - [Installation Requirements / Dependencies](#installation-requirements--dependencies)

  - [For Users](#for-users)

    - [Quick Links](#quick-links)

    - [Windows Quick Start with Claude Code](#windows-quick-start-with-claude-code)

      - [1. Install the MCP server](#1-install-the-mcp-server)

      - [2. Connect Claude Code to the server](#2-connect-claude-code-to-the-server)

      - [3. Start FreeCAD with the bridge using start-mcp-and-freecad.cmd](#3-start-freecad-with-the-bridge-using-start-mcp-and-freecadcmd)

      - [4. The freecad modeling skill](#4-the-freecad-modeling-skill)

  - [Robust MCP Server](#robust-mcp-server)

    - [Installation](#installation)

      - [Using pip (recommended)](#using-pip-recommended)

      - [Using mise and just (from source)](#using-mise-and-just-from-source)

      - [Using Docker](#using-docker)

    - [Configuration](#configuration)

      - [Environment Variables](#environment-variables)

      - [Connection Modes](#connection-modes)

      - [MCP Client Configuration](#mcp-client-configuration)

    - [Usage](#usage)

      - [Starting the MCP Bridge in FreeCAD](#starting-the-mcp-bridge-in-freecad)

        - [Option A: Using the Workbench (Recommended)](#option-a-using-the-workbench-recommended)

        - [Option B: Using just commands (from source)](#option-b-using-just-commands-from-source)

      - [Uninstalling the MCP Bridge](#uninstalling-the-mcp-bridge)

        - [Checking for Legacy Components](#checking-for-legacy-components)

        - [Manual Cleanup (if needed)](#manual-cleanup-if-needed)

      - [Running Modes](#running-modes)

        - [XML-RPC Mode (Recommended)](#xml-rpc-mode-recommended)

        - [Socket Mode (JSON-RPC)](#socket-mode-json-rpc)

        - [Headless Mode](#headless-mode)

        - [Embedded Mode (Linux Only)](#embedded-mode-linux-only)

    - [Available Tools](#available-tools)

      - [Execution & Debugging (5 tools)](#execution--debugging-5-tools)

      - [Document Management (7 tools)](#document-management-7-tools)

      - [Object Creation - Primitives (8 tools)](#object-creation---primitives-8-tools)

      - [Object Management (12 tools)](#object-management-12-tools)

      - [PartDesign - Sketching (14 tools)](#partdesign---sketching-14-tools)

      - [PartDesign - Patterns & Edges (5 tools)](#partdesign---patterns--edges-5-tools)

      - [View & Display (11 tools)](#view--display-11-tools)

      - [Undo/Redo (3 tools)](#undoredo-3-tools)

      - [Export/Import (7 tools)](#exportimport-7-tools)

      - [Macro Management (6 tools)](#macro-management-6-tools)

      - [Parts Library (2 tools)](#parts-library-2-tools)

  - [For Developers](#for-developers)

  - [Robust MCP Server Development](#robust-mcp-server-development)

    - [Prerequisites](#prerequisites)

    - [Initial Setup](#initial-setup)

    - [MCP Client Configuration (Development)](#mcp-client-configuration-development)

    - [Development Workflow](#development-workflow)

    - [Running FreeCAD with the MCP Bridge](#running-freecad-with-the-mcp-bridge)

      - [GUI Mode (recommended for development)](#gui-mode-recommended-for-development)

      - [Headless Mode (for automation/CI)](#headless-mode-for-automationci)

    - [Running Tests](#running-tests)

    - [Code Quality](#code-quality)

  - [Architecture](#architecture)

  - [Acknowledgements](#acknowledgements)

    - [Related Projects](#related-projects)

  - [License](#license)


<!--TOC-->


> The macros that were originally in this repo under the `/macros` directory have been permanently moved to two new GitHub repos:
>
> - [spkane/freecad-macro-cut-for-magnets](https://github.com/spkane/freecad-macro-cut-for-magnets)
> - [spkane/freecad-macro-3d-print-multi-export](https://github.com/spkane/freecad-macro-3d-print-multi-export)

**FreeCAD Forum:** [addon discussion post](https://forum.freecad.org/viewtopic.php?p=866012)

## Features

- **150+ MCP Tools**: Comprehensive CAD operations including primitives, PartDesign, booleans, export
- **Multiple Connection Modes**: XML-RPC (recommended), JSON-RPC socket, or embedded
- **GUI & Headless Support**: Full modeling in headless mode, plus screenshots/colors in GUI mode
- **Macro Development**: Create, edit, run, and template FreeCAD macros via MCP

## Installation Requirements / Dependencies

- [FreeCAD](https://www.freecadweb.org/) 0.21+ or 1.0+
- Python 3.11 (required for FreeCAD ABI compatibility)

---

## For Users

This section covers installation and usage for end users who want to use the Robust MCP Server with AI assistants.

### Quick Links

| Resource                                                                              | Description                                   |
| ------------------------------------------------------------------------------------- | --------------------------------------------- |
| [**Documentation**](https://spkane.github.io/freecad-addon-robust-mcp-server/)        | Full documentation, guides, and API reference |
| [Docker Hub](https://hub.docker.com/r/spkane/freecad-robust-mcp)                      | Pre-built Docker images for easy deployment   |
| [PyPI](https://pypi.org/project/freecad-robust-mcp/)                                  | Python package for pip installation           |
| [GitHub Releases](https://github.com/spkane/freecad-addon-robust-mcp-server/releases) | Release archives and changelogs               |

### Windows Quick Start with Claude Code

This fork adds a Windows-oriented workflow for using the server from
[Claude Code](https://docs.anthropic.com/en/docs/claude-code) together with a bundled
FreeCAD modeling skill.

#### 1. Install the MCP server

Install [uv](https://docs.astral.sh/uv/) (`winget install astral-sh.uv`), then
install the server straight from this fork so its tool fixes are used (the PyPI
package also works, but lags behind):

```powershell
uv tool install git+https://github.com/LordBoos/freecad-addon-robust-mcp-server
```

`uv tool install` puts a `freecad-mcp` executable on your PATH. Run
`uv tool upgrade freecad-robust-mcp` to pick up new commits. You still need a copy
of the repository for the FreeCAD side (the bridge startup script used by
`start-mcp-and-freecad.cmd`): clone it with `git clone` or download the GitHub ZIP.

If you prefer installing from a local checkout, run `uv tool install .` inside it. The
package version comes from git tags, so a `git clone` works directly; a GitHub ZIP
download has no `.git` folder and installs as version `0.0.0+local`, which is fine for
use with Claude Code.

#### 2. Connect Claude Code to the server

Create `.mcp.json` in the directory where you run Claude Code (this repository, or
your own project folder), or register the server globally with
`claude mcp add --scope user freecad -- freecad-mcp --mode xmlrpc`:

```json
{
  "mcpServers": {
    "freecad": {
      "command": "freecad-mcp",
      "args": ["--mode", "xmlrpc"],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

`PYTHONIOENCODING=utf-8` avoids console-encoding errors on Windows when FreeCAD
returns non-ASCII text. The server connects to the bridge on `localhost:9875`, so
FreeCAD must be running with the bridge started (next step). Check with `/mcp` inside
Claude Code that `freecad` shows as connected.

#### 3. Start FreeCAD with the bridge using start-mcp-and-freecad.cmd

Double-click `start-mcp-and-freecad.cmd` or run it from a terminal. It starts the
FreeCAD GUI directly with the bridge startup script, so the bridge is listening as soon
as FreeCAD is up (typically 10-30 s). It needs nothing but FreeCAD 1.x installed; `just`
and Git Bash are not required for this script.

The script looks for FreeCAD in the usual locations (`C:\Program Files\FreeCAD 1.1`,
`C:\Program Files\FreeCAD 1.0`, and the per-user `%LOCALAPPDATA%\Programs` variants).
To use a different FreeCAD location set `FREECAD_EXE` first:

```powershell
$env:FREECAD_EXE = "D:\Apps\FreeCAD\bin\freecad.exe"
.\start-mcp-and-freecad.cmd
```

The script only starts FreeCAD. The MCP server process is started by Claude Code from
`.mcp.json`, and it reconnects automatically once the bridge is up. If Claude Code was
started before FreeCAD, the `get_connection_status` tool reports `connected: false`
until FreeCAD is running; no restart of Claude Code is needed.

The same can be done by hand, which is all the script does:

```powershell
& "C:\Program Files\FreeCAD 1.1\bin\freecad.exe" ".\freecad\RobustMCPBridge\freecad_mcp_bridge\startup_bridge.py"
```

The `just` recipes (`just freecad::run-gui` and friends) are for development. On
Windows they run in Git Bash and `just` needs `cygpath` from Git for Windows on the
PATH; if you see an error about `cygpath` not being found, add
`C:\Program Files\Git\usr\bin` to your PATH or run `just` from a Git Bash terminal.

#### 4. The freecad modeling skill

The repository ships a Claude Code skill in `.claude/skills/freecad/`. It is loaded
automatically when Claude Code runs inside this repository, and it teaches Claude how
to model parametrically with the MCP tools: PartDesign-first workflows, geometric
selection of faces and edges instead of guessed indices, numeric verification with
`BoundBox` and `Volume`, a FreeCAD 1.1 compatibility matrix for the MCP tools, print
quality STL export, and a headless fallback via `freecadcmd.exe` when the MCP server
is not connected. The skill also knows how to start FreeCAD itself with
`start-mcp-and-freecad.cmd` when the bridge is not reachable.

To use the skill from any other project, copy or link the folder into your user
skills directory:

```powershell
Copy-Item -Recurse .claude\skills\freecad "$env:USERPROFILE\.claude\skills\freecad"
```

Then just ask, for example: "Design a 40x40 mm enclosure with M3 mounting holes and
export it as STL". Claude will invoke the skill, probe the connection, create a
PartDesign body, and verify each feature numerically.

Paths inside `SKILL.md` written as `<repo>` refer to the checkout root; the FreeCAD
executable path and the Bambu Studio slicer path are specific to a typical Windows
installation and can be edited to match your machine.

## Robust MCP Server

> **Note**: The Linux container and PyPI package are both named `freecad-robust-mcp` which differs slightly from this git repository name.

### Installation

#### Using pip (recommended)

```bash
pip install freecad-robust-mcp
```

#### Using mise and just (from source)

```bash
git clone https://github.com/spkane/freecad-addon-robust-mcp-server.git
cd freecad-addon-robust-mcp-server

# Install mise via the Official mise installer script (if not already installed)
curl https://mise.run | sh

mise trust
mise install
just setup
```

#### Using Docker

Run the Robust MCP Server in a container. This is useful for isolated environments or when you don't want to install Python dependencies on your host.

```bash
# Pull from Docker Hub (when published)
docker pull spkane/freecad-robust-mcp

# Or build locally
git clone https://github.com/spkane/freecad-addon-robust-mcp-server.git
cd freecad-addon-robust-mcp-server
docker build -t freecad-robust-mcp .

# Or use just commands (if you have mise/just installed)
just docker::build        # Build for local architecture
just docker::build-multi  # Build multi-arch (amd64 + arm64)
```

**Note:** The containerized Robust MCP Server only supports `xmlrpc` and `socket` modes since FreeCAD runs on your host machine (not in the container). The container connects to FreeCAD via `host.docker.internal`.

### Configuration

#### Environment Variables

| Variable              | Description                                          | Default     |
| --------------------- | ---------------------------------------------------- | ----------- |
| `FREECAD_MODE`        | Connection mode: `xmlrpc`, `socket`, or `embedded`   | `xmlrpc`    |
| `FREECAD_PATH`        | Path to FreeCAD's lib directory (embedded mode only) | Auto-detect |
| `FREECAD_SOCKET_HOST` | Socket/XML-RPC server hostname                       | `localhost` |
| `FREECAD_SOCKET_PORT` | JSON-RPC socket server port                          | `9876`      |
| `FREECAD_XMLRPC_PORT` | XML-RPC server port                                  | `9875`      |
| `FREECAD_TIMEOUT_MS`  | Execution timeout in ms                              | `30000`     |

#### Connection Modes

| Mode       | Description                                 | Platform Support                  |
| ---------- | ------------------------------------------- | --------------------------------- |
| `xmlrpc`   | Connects to FreeCAD via XML-RPC (port 9875) | **All platforms** (recommended)   |
| `socket`   | Connects via JSON-RPC socket (port 9876)    | **All platforms**                 |
| `embedded` | Imports FreeCAD directly into process       | **Linux only** (crashes on macOS) |

**Note:** Embedded mode crashes on macOS because FreeCAD's `FreeCAD.so` links to `@rpath/libpython3.11.dylib`, which conflicts with external Python interpreters. Use `xmlrpc` or `socket` mode on macOS and Windows.

#### MCP Client Configuration

Add something like the following to your MCP client settings. For Claude Code, this is `~/.claude/claude_desktop_config.json` or a project `.mcp.json` file:

```json
{
  "mcpServers": {
    "freecad": {
      "command": "freecad-mcp",
      "env": {
        "FREECAD_MODE": "xmlrpc"
      }
    }
  }
}
```

If installed from source with mise/uv:

```json
{
  "mcpServers": {
    "freecad": {
      "command": "/path/to/mise/shims/uv",
      "args": ["run", "--project", "/path/to/freecad-addon-robust-mcp-server", "freecad-mcp"],
      "env": {
        "FREECAD_MODE": "xmlrpc"
      }
    }
  }
}
```

If using Docker:

```json
{
  "mcpServers": {
    "freecad": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--add-host=host.docker.internal:host-gateway",
        "-e", "FREECAD_MODE=xmlrpc",
        "-e", "FREECAD_SOCKET_HOST=host.docker.internal",
        "spkane/freecad-robust-mcp"
      ]
    }
  }
}
```

**Docker configuration notes:**

- `--rm` removes the container after it exits
- `-i` keeps stdin open for MCP communication
- `--add-host=host.docker.internal:host-gateway` allows the container to connect to FreeCAD on your host (Linux only; macOS/Windows have this built-in)
- `FREECAD_SOCKET_HOST=host.docker.internal` tells the Robust MCP Server to connect to FreeCAD on your host machine

### Usage

#### Starting the MCP Bridge in FreeCAD

Before your AI assistant can connect, you need to start the MCP bridge inside FreeCAD:

##### Option A: Using the Workbench (Recommended)

1. Install the Robust MCP Bridge workbench via FreeCAD's Addon Manager:

   - **Edit -> Preferences -> Addon Manager**
   - Search for "Robust MCP Bridge"
   - Install and restart FreeCAD

1. Start the bridge:

   - Switch to the Robust MCP Bridge workbench
   - Click the **Start MCP Bridge** button in the toolbar
   - Or use the menu: **MCP Bridge -> Start Bridge**

1. You should see in the FreeCAD console:

   ```text
   MCP Bridge started!
     - XML-RPC: localhost:9875
     - Socket: localhost:9876
   ```

##### Option B: Using just commands (from source)

```bash
# Start FreeCAD with MCP bridge auto-started
just freecad::run-gui

# Or for headless/automation mode:
just freecad::run-headless
```

After starting the bridge, start/restart your MCP client (Claude Code, etc.) - it will connect automatically

#### Uninstalling the MCP Bridge

To uninstall the Robust MCP Bridge workbench:

1. Open FreeCAD
1. Go to **Edit -> Preferences -> Addon Manager**
1. Find "Robust MCP Bridge" in the list
1. Click **Uninstall**
1. Restart FreeCAD

##### Checking for Legacy Components

If you previously used older versions of this project, you may have legacy components installed. Run this command to check what's installed and get cleanup instructions:

```bash
just install::status
```

##### Manual Cleanup (if needed)

Remove any legacy files that may conflict with the workbench:

```bash
# macOS - remove legacy plugin and macro
rm -rf ~/Library/Application\ Support/FreeCAD/Mod/MCPBridge/
rm -f ~/Library/Application\ Support/FreeCAD/Macro/StartMCPBridge.FCMacro

# Linux - remove legacy plugin and macro
rm -rf ~/.local/share/FreeCAD/Mod/MCPBridge/
rm -f ~/.local/share/FreeCAD/Macro/StartMCPBridge.FCMacro
```

#### Running Modes

##### XML-RPC Mode (Recommended)

Connects to a running FreeCAD instance via XML-RPC. Works on all platforms.

```bash
FREECAD_MODE=xmlrpc freecad-mcp
```

##### Socket Mode (JSON-RPC)

Connects via JSON-RPC socket. Works on all platforms.

```bash
FREECAD_MODE=socket freecad-mcp
```

##### Headless Mode

Run FreeCAD in console mode without GUI. Useful for automation.

```bash
# If installed from source:
just freecad::run-headless
```

**Note:** Screenshot and view features are not available in headless mode.

##### Embedded Mode (Linux Only)

Runs FreeCAD in-process. **Only works on Linux** - crashes on macOS/Windows.

```bash
FREECAD_MODE=embedded freecad-mcp
```

### Available Tools

The Robust MCP Server provides **150+ tools** organized into categories. Tools marked with **GUI** require FreeCAD to be running in GUI mode; they will return an error in headless mode.

#### Execution & Debugging (5 tools)

| Tool                         | Description                                                   | Mode |
| ---------------------------- | ------------------------------------------------------------- | ---- |
| `execute_python`             | Execute arbitrary Python code in FreeCAD's context            | All  |
| `get_freecad_version`        | Get FreeCAD version, build date, and Python version           | All  |
| `get_connection_status`      | Check MCP bridge connection status and latency                | All  |
| `get_console_output`         | Get recent FreeCAD console output (up to N lines)             | All  |
| `get_mcp_server_environment` | Get Robust MCP Server environment (OS, hostname, instance_id) | All  |

#### Document Management (7 tools)

| Tool                  | Description                               | Mode |
| --------------------- | ----------------------------------------- | ---- |
| `list_documents`      | List all open documents with metadata     | All  |
| `get_active_document` | Get information about the active document | All  |
| `create_document`     | Create a new FreeCAD document             | All  |
| `open_document`       | Open an existing .FCStd file              | All  |
| `save_document`       | Save a document to disk                   | All  |
| `close_document`      | Close a document (with optional save)     | All  |
| `recompute_document`  | Force recomputation of all objects        | All  |

#### Object Creation - Primitives (8 tools)

| Tool              | Description                                        | Mode |
| ----------------- | -------------------------------------------------- | ---- |
| `create_object`   | Create a generic FreeCAD object by type ID         | All  |
| `create_box`      | Create a Part::Box with length, width, height      | All  |
| `create_cylinder` | Create a Part::Cylinder with radius, height, angle | All  |
| `create_sphere`   | Create a Part::Sphere with radius                  | All  |
| `create_cone`     | Create a Part::Cone with two radii and height      | All  |
| `create_torus`    | Create a Part::Torus (donut) with radii and angles | All  |
| `create_wedge`    | Create a Part::Wedge (tapered box)                 | All  |
| `create_helix`    | Create a Part::Helix curve for sweeps and threads  | All  |

#### Object Management (12 tools)

| Tool                | Description                                        | Mode |
| ------------------- | -------------------------------------------------- | ---- |
| `list_objects`      | List all objects in a document                     | All  |
| `inspect_object`    | Get detailed object info (properties, shape, etc.) | All  |
| `edit_object`       | Modify properties of an existing object            | All  |
| `delete_object`     | Delete an object from a document                   | All  |
| `set_placement`     | Set object position and rotation                   | All  |
| `scale_object`      | Scale an object uniformly or non-uniformly         | All  |
| `rotate_object`     | Rotate an object around an axis                    | All  |
| `copy_object`       | Create a copy of an object                         | All  |
| `mirror_object`     | Mirror an object across a plane (XY, XZ, YZ)       | All  |
| `boolean_operation` | Fuse, cut, or intersect objects                    | All  |
| `get_selection`     | Get currently selected objects                     | GUI  |
| `set_selection`     | Select specific objects by name                    | GUI  |
| `clear_selection`   | Clear all selections                               | GUI  |

#### PartDesign - Sketching (14 tools)

| Tool                     | Description                                     | Mode |
| ------------------------ | ----------------------------------------------- | ---- |
| `create_partdesign_body` | Create a PartDesign::Body container             | All  |
| `create_sketch`          | Create a sketch on a plane or face              | All  |
| `add_sketch_rectangle`   | Add a rectangle to a sketch                     | All  |
| `add_sketch_circle`      | Add a circle to a sketch                        | All  |
| `add_sketch_line`        | Add a line (with optional construction flag)    | All  |
| `add_sketch_arc`         | Add an arc by center, radius, and angles        | All  |
| `add_sketch_point`       | Add a point (useful for hole centers)           | All  |
| `pad_sketch`             | Extrude a sketch (additive)                     | All  |
| `pocket_sketch`          | Cut into solid using a sketch (subtractive)     | All  |
| `revolution_sketch`      | Revolve a sketch around an axis (additive)      | All  |
| `groove_sketch`          | Revolve a sketch around an axis (subtractive)   | All  |
| `create_hole`            | Create parametric holes with optional threading | All  |
| `loft_sketches`          | Create a loft through multiple sketches         | All  |
| `sweep_sketch`           | Sweep a profile along a spine path              | All  |

#### PartDesign - Patterns & Edges (5 tools)

| Tool               | Description                                | Mode |
| ------------------ | ------------------------------------------ | ---- |
| `linear_pattern`   | Create linear pattern of a feature         | All  |
| `polar_pattern`    | Create polar/circular pattern of a feature | All  |
| `mirrored_feature` | Mirror a feature across a plane            | All  |
| `fillet_edges`     | Add fillets (rounded edges)                | All  |
| `chamfer_edges`    | Add chamfers (beveled edges)               | All  |

#### View & Display (11 tools)

| Tool                    | Description                                     | Mode |
| ----------------------- | ----------------------------------------------- | ---- |
| `get_screenshot`        | Capture a screenshot of the 3D view             | GUI  |
| `set_view_angle`        | Set camera to standard views (Front, Top, etc.) | GUI  |
| `fit_all`               | Zoom to fit all objects in view                 | GUI  |
| `zoom_in`               | Zoom in by a factor                             | GUI  |
| `zoom_out`              | Zoom out by a factor                            | GUI  |
| `set_camera_position`   | Set camera position and look-at point           | GUI  |
| `set_object_visibility` | Show/hide objects                               | GUI  |
| `set_display_mode`      | Set display mode (Shaded, Wireframe, etc.)      | GUI  |
| `set_object_color`      | Set object color as RGB values                  | GUI  |
| `list_workbenches`      | List available FreeCAD workbenches              | All  |
| `activate_workbench`    | Switch to a different workbench                 | All  |

#### Undo/Redo (3 tools)

| Tool                   | Description                        | Mode |
| ---------------------- | ---------------------------------- | ---- |
| `undo`                 | Undo the last operation            | All  |
| `redo`                 | Redo a previously undone operation | All  |
| `get_undo_redo_status` | Get available undo/redo operations | All  |

#### Export/Import (7 tools)

| Tool          | Description                                | Mode |
| ------------- | ------------------------------------------ | ---- |
| `export_step` | Export to STEP format (ISO CAD exchange)   | All  |
| `export_stl`  | Export to STL format (3D printing)         | All  |
| `export_3mf`  | Export to 3MF format (modern 3D printing)  | All  |
| `export_obj`  | Export to OBJ format (Wavefront)           | All  |
| `export_iges` | Export to IGES format (older CAD exchange) | All  |
| `import_step` | Import a STEP file                         | All  |
| `import_stl`  | Import an STL file as mesh                 | All  |

#### Macro Management (6 tools)

| Tool                         | Description                                    | Mode |
| ---------------------------- | ---------------------------------------------- | ---- |
| `list_macros`                | List all available FreeCAD macros              | All  |
| `run_macro`                  | Execute a macro by name                        | All  |
| `create_macro`               | Create a new macro file                        | All  |
| `read_macro`                 | Read macro source code                         | All  |
| `delete_macro`               | Delete a user macro                            | All  |
| `create_macro_from_template` | Create macro from template (basic, part, etc.) | All  |

#### Parts Library (2 tools)

| Tool                       | Description                           | Mode |
| -------------------------- | ------------------------------------- | ---- |
| `list_parts_library`       | List parts in FreeCAD's parts library | All  |
| `insert_part_from_library` | Insert a part from the library        | All  |

---

## For Developers

This section covers development setup, contributing, and working with the codebase.

## Robust MCP Server Development

### Prerequisites

- [mise](https://mise.jdx.dev/) - Tool version manager
- [FreeCAD](https://www.freecadweb.org/) 0.21+ or 1.0+

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/spkane/freecad-addon-robust-mcp-server.git
cd freecad-addon-robust-mcp-server

# Install mise via the Official mise installer script (if not already installed)
curl https://mise.run | sh

# Install all tools (Python 3.11, uv, just, pre-commit)
mise trust
mise install

# Set up the development environment
just setup
```

This installs:

- **Python 3.11** - Required for FreeCAD ABI compatibility
- **uv** - Fast Python package manager
- **just** - Command runner for development workflows
- **pre-commit** - Git hooks for code quality

### MCP Client Configuration (Development)

Create a `.mcp.json` file in the project directory:

```json
{
  "mcpServers": {
    "freecad": {
      "command": "/path/to/mise/shims/uv",
      "args": ["run", "--project", "/path/to/freecad-addon-robust-mcp-server", "freecad-mcp"],
      "env": {
        "FREECAD_MODE": "xmlrpc",
        "FREECAD_SOCKET_HOST": "localhost",
        "FREECAD_XMLRPC_PORT": "9875",
        "PATH": "/path/to/mise/shims:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
      }
    }
  }
}
```

**Replace the paths with your actual paths:**

| Placeholder                                 | Description                     | Example                                        |
| ------------------------------------------- | ------------------------------- | ---------------------------------------------- |
| `/path/to/mise/shims/uv`                    | Full path to uv via mise shims  | `~/.local/share/mise/shims/uv`                 |
| `/path/to/freecad-addon-robust-mcp-server`  | Project directory               | `/home/me/dev/freecad-addon-robust-mcp-server` |
| `/path/to/mise/shims`                       | mise shims directory for PATH   | `~/.local/share/mise/shims`                    |

**Finding your mise shims path:**

```bash
mise where uv | sed 's|/installs/.*|/shims|'
# Example: /home/user/.local/share/mise/shims (on Linux) or ~/.local/share/mise/shims (on macOS)
```

### Development Workflow

Commands are organized into modules. Use `just` to see top-level commands, or `just list-<module>` to see module-specific commands.

```bash
# Show top-level commands and available modules
just

# Show commands in a specific module
just list-mcp           # Robust MCP Server commands
just list-freecad       # FreeCAD plugin/macro commands
just list-install       # Installation commands
just list-quality       # Code quality commands
just list-testing       # Test commands
just list-docker        # Docker commands
just list-documentation # Documentation commands
just list-dev           # Development utilities

# List ALL commands from all modules
just list-all

# Install/update dependencies
just install::mcp-server

# Run all checks (linting, type checking, tests)
just all

# Quality commands
just quality::lint       # Run ruff linter
just quality::typecheck  # Run mypy type checker
just quality::format     # Format code
just quality::check      # Run all pre-commit hooks

# Testing commands
just testing::unit       # Run unit tests
just testing::cov        # Run tests with coverage
just testing::integration # Run integration tests

# Run the Robust MCP Server (or with debug logging)
just mcp::run
just mcp::run-debug

# Docker commands
just docker::build        # Build image for local architecture
just docker::build-multi  # Build multi-arch image (amd64 + arm64)
just docker::run          # Run container
```

### Running FreeCAD with the MCP Bridge

#### GUI Mode (recommended for development)

```bash
# Start FreeCAD with auto-started bridge
just freecad::run-gui
```

#### Headless Mode (for automation/CI)

```bash
just freecad::run-headless
```

### Running Tests

```bash
# Unit tests only (no FreeCAD required)
just testing::unit

# Unit tests with coverage
just testing::cov

# Integration tests (requires running FreeCAD bridge)
just testing::integration

# Integration tests with automatic FreeCAD startup
just testing::integration-auto
```

### Code Quality

The project uses strict code quality checks via pre-commit:

- **Ruff** - Linting and formatting
- **MyPy** - Type checking
- **Bandit** - Security scanning
- **Codespell** - Spell checking
- **Secrets scanning** - Gitleaks, detect-secrets, TruffleHog

```bash
# Run all pre-commit hooks
just quality::check

# Run security/secrets scans
just quality::security
just quality::secrets
```

---

## Architecture

See the [detailed architecture document](docs/development/architecture-detailed.md) for design documentation covering:

- Module structure
- Bridge communication protocols
- Tool registration patterns
- FreeCAD plugin architecture

---

## Acknowledgements

This project was developed after analyzing several existing FreeCAD Robust MCP implementations. We are grateful to these projects for their pioneering work and the ideas they contributed to the FreeCAD + AI ecosystem:

### Related Projects

- **[neka-nat/freecad-mcp](https://github.com/neka-nat/freecad-mcp)** (MIT License) - The queue-based thread safety pattern and XML-RPC protocol design (port 9875) were directly inspired by this project. Our implementation maintains protocol compatibility while being a complete rewrite with additional features.

- **[jango-blockchained/mcp-freecad](https://github.com/jango-blockchained/mcp-freecad)** - Inspired our connection recovery mechanisms and multi-mode architecture approach.

- **[contextform/freecad-mcp](https://github.com/contextform/freecad-mcp)** - Informed our comprehensive PartDesign and Part workbench tool coverage.

- **[ATOI-Ming/FreeCAD-MCP](https://github.com/ATOI-Ming/FreeCAD-MCP)** - Inspired our macro development toolkit including templates, validation, and automatic imports.

- **[bonninr/freecad_mcp](https://github.com/bonninr/freecad_mcp)** - Influenced our simple socket-based communication approach.

See [docs/COMPARISON.md](docs/COMPARISON.md) for a detailed analysis of these implementations and the design decisions they informed.

---

## License

MIT License - see [LICENSE](LICENSE) for details.
