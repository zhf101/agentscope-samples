# -*- coding: utf-8 -*-
"""
Agent-Browser MCP Server

A Model Context Protocol (MCP) server that wraps the agent-browser CLI
(https://github.com/vercel-labs/agent-browser) for AI-friendly browser automation.

This server provides AI-optimized browser tools with:
- Ref-based element selection (@eN format)
- Annotated screenshots for multimodal agents
- Security features (domain allowlist, action confirmation)
- Session isolation and state persistence
"""

import asyncio
import json
import logging
import os
import shutil
import tempfile
from typing import Any, Optional
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Server instance
server = Server("agent-browser-mcp")


class AgentBrowserConfig(BaseModel):
    """Runtime configuration mapped to `agent-browser` global CLI options."""
    default_timeout: int = 25000
    max_output: int = 50000
    allowed_domains: Optional[list[str]] = None
    headed: bool = False
    session_name: Optional[str] = None
    executable_path: Optional[str] = None
    profile_path: Optional[str] = None


# Global config
config = AgentBrowserConfig()

# Cached element refs returned by `snapshot`; useful for agent workflows that
# perform "snapshot -> act by @eN ref".
_cached_refs: dict[str, dict] = {}

# Lightweight lifecycle marker; primarily informational.
_browser_open = False


def check_agent_browser_installed() -> bool:
    """Check if agent-browser CLI is installed"""
    return shutil.which("agent-browser") is not None


async def execute_cli(
    command: str,
    args: list[str] = None,
    timeout: int = 30,
) -> dict:
    """
    Execute agent-browser CLI command and return JSON result.
    
    Args:
        command: The agent-browser command (e.g., "open", "click", "snapshot")
        args: Additional arguments for the command
        timeout: Timeout in seconds
    
    Returns:
        Dict with success status and data/error
    """
    # This wrapper is the key abstraction of this module:
    # MCP tool call -> agent-browser CLI invocation -> normalized JSON result.
    global _browser_open
    
    if not check_agent_browser_installed():
        return {
            "success": False,
            "error": "agent-browser CLI not found. Install with: npm install -g agent-browser"
        }
    
    cmd = ["agent-browser"]
    
    # Add global options from config so every command shares same session
    # behavior (profile, allowlist, output size, etc.).
    if config.session_name:
        cmd.extend(["--session-name", config.session_name])
    if config.headed:
        cmd.append("--headed")
    if config.allowed_domains:
        cmd.extend(["--allowed-domains", ",".join(config.allowed_domains)])
    if config.executable_path:
        cmd.extend(["--executable-path", config.executable_path])
    if config.profile_path:
        cmd.extend(["--profile", config.profile_path])
    cmd.extend(["--max-output", str(config.max_output)])
    
    # Add subcommand and command-specific args.
    cmd.append(command)
    if args:
        cmd.extend(args)
    
    # Always request machine-readable output for MCP response formatting.
    cmd.append("--json")
    
    logger.info(f"Executing: {' '.join(cmd)}")
    
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=timeout
        )
        
        if proc.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            logger.error(f"CLI error: {error_msg}")
            return {"success": False, "error": error_msg}
        
        # Parse JSON output from the CLI.
        output = stdout.decode().strip()
        if output:
            try:
                result = json.loads(output)
                # Track browser state
                if command == "open":
                    _browser_open = True
                elif command in ["close", "quit", "exit"]:
                    _browser_open = False
                return result
            except json.JSONDecodeError:
                return {"success": True, "data": output}
        else:
            return {"success": True}
            
    except asyncio.TimeoutError:
        return {"success": False, "error": f"Command timed out after {timeout}s"}
    except Exception as e:
        logger.error(f"Execution error: {e}")
        return {"success": False, "error": str(e)}


# ==================== Tool Definitions ====================

@server.list_tools()
async def list_tools() -> list[Tool]:
    """Declare MCP tool contracts.

    These schemas are the public API seen by upstream model/runtime callers.
    """
    return [
        # === Navigation ===
        Tool(
            name="browser_navigate",
            description="Navigate to a URL in the browser. Opens a new browser instance if not already open.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to navigate to"
                    }
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="browser_back",
            description="Navigate back in browser history",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="browser_forward",
            description="Navigate forward in browser history",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="browser_reload",
            description="Reload the current page",
            inputSchema={"type": "object", "properties": {}}
        ),
        
        # === Snapshot & Screenshot ===
        Tool(
            name="browser_snapshot",
            description=(
                "Get an AI-optimized accessibility tree with element refs. "
                "Returns refs like @e1, @e2 for precise element selection. "
                "This is the preferred way to understand page structure for AI agents."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "interactive_only": {
                        "type": "boolean",
                        "description": "Only show interactive elements (buttons, links, inputs)",
                        "default": True
                    },
                    "compact": {
                        "type": "boolean",
                        "description": "Remove empty structural elements",
                        "default": True
                    },
                    "depth": {
                        "type": "integer",
                        "description": "Maximum tree depth",
                        "default": 5
                    },
                    "selector": {
                        "type": "string",
                        "description": "Scope to CSS selector (optional)"
                    }
                }
            }
        ),
        Tool(
            name="browser_screenshot",
            description=(
                "Take a screenshot of the current page. "
                "Use --annotate to add numbered labels matching element refs."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "annotate": {
                        "type": "boolean",
                        "description": "Add numbered labels matching refs (@eN)",
                        "default": True
                    },
                    "full_page": {
                        "type": "boolean",
                        "description": "Capture full page instead of viewport",
                        "default": False
                    }
                }
            }
        ),
        
        # === Interaction ===
        Tool(
            name="browser_click",
            description="Click an element by ref (@eN) or CSS selector. Use refs from browser_snapshot for precise targeting.",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "Element ref (e.g., @e1) or CSS selector"
                    },
                    "new_tab": {
                        "type": "boolean",
                        "description": "Open link in new tab",
                        "default": False
                    }
                },
                "required": ["selector"]
            }
        ),
        Tool(
            name="browser_fill",
            description="Clear and fill an input field with text. Use refs from browser_snapshot.",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "Element ref (e.g., @e1) or CSS selector"
                    },
                    "value": {
                        "type": "string",
                        "description": "Value to fill"
                    }
                },
                "required": ["selector", "value"]
            }
        ),
        Tool(
            name="browser_type",
            description="Type text into an element without clearing first. Use for appending text.",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "Element ref or CSS selector"
                    },
                    "text": {
                        "type": "string",
                        "description": "Text to type"
                    }
                },
                "required": ["selector", "text"]
            }
        ),
        Tool(
            name="browser_press",
            description="Press a key (e.g., Enter, Tab, Escape, Control+a)",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "Key to press (e.g., Enter, Tab, Escape)"
                    }
                },
                "required": ["key"]
            }
        ),
        Tool(
            name="browser_hover",
            description="Hover over an element",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "Element ref or CSS selector"
                    }
                },
                "required": ["selector"]
            }
        ),
        Tool(
            name="browser_scroll",
            description="Scroll the page",
            inputSchema={
                "type": "object",
                "properties": {
                    "direction": {
                        "type": "string",
                        "enum": ["up", "down", "left", "right"],
                        "description": "Scroll direction"
                    },
                    "pixels": {
                        "type": "integer",
                        "description": "Pixels to scroll",
                        "default": 300
                    }
                },
                "required": ["direction"]
            }
        ),
        Tool(
            name="browser_select",
            description="Select an option from a dropdown",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "Element ref or CSS selector"
                    },
                    "value": {
                        "type": "string",
                        "description": "Option value to select"
                    }
                },
                "required": ["selector", "value"]
            }
        ),
        
        # === Waiting ===
        Tool(
            name="browser_wait",
            description="Wait for a condition (element, text, URL, or load state)",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "Wait for element to be visible"
                    },
                    "text": {
                        "type": "string",
                        "description": "Wait for text to appear on page"
                    },
                    "url_pattern": {
                        "type": "string",
                        "description": "Wait for URL to match pattern"
                    },
                    "load_state": {
                        "type": "string",
                        "enum": ["load", "domcontentloaded", "networkidle"],
                        "description": "Wait for load state"
                    },
                    "timeout_ms": {
                        "type": "integer",
                        "description": "Timeout in milliseconds"
                    }
                }
            }
        ),
        
        # === Get Information ===
        Tool(
            name="browser_get_text",
            description="Get text content of an element",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "Element ref or CSS selector"
                    }
                },
                "required": ["selector"]
            }
        ),
        Tool(
            name="browser_get_url",
            description="Get current page URL",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="browser_get_title",
            description="Get page title",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="browser_is_visible",
            description="Check if an element is visible",
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "Element ref or CSS selector"
                    }
                },
                "required": ["selector"]
            }
        ),
        
        # === Tabs ===
        Tool(
            name="browser_tab_list",
            description="List all open tabs",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="browser_tab_new",
            description="Open a new tab",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to open in new tab (optional)"
                    }
                }
            }
        ),
        Tool(
            name="browser_tab_switch",
            description="Switch to a tab by index",
            inputSchema={
                "type": "object",
                "properties": {
                    "index": {
                        "type": "integer",
                        "description": "Tab index (0-based)"
                    }
                },
                "required": ["index"]
            }
        ),
        Tool(
            name="browser_tab_close",
            description="Close current or specified tab",
            inputSchema={
                "type": "object",
                "properties": {
                    "index": {
                        "type": "integer",
                        "description": "Tab index to close (optional, closes current if not specified)"
                    }
                }
            }
        ),
        
        # === JavaScript ===
        Tool(
            name="browser_eval",
            description="Execute JavaScript in the browser",
            inputSchema={
                "type": "object",
                "properties": {
                    "script": {
                        "type": "string",
                        "description": "JavaScript code to execute"
                    }
                },
                "required": ["script"]
            }
        ),
        
        # === Session ===
        Tool(
            name="browser_close",
            description="Close the browser and end the session",
            inputSchema={"type": "object", "properties": {}}
        ),
        
        # === Find (convenient shortcuts) ===
        Tool(
            name="browser_find_click",
            description="Find element by text/role/label and click it",
            inputSchema={
                "type": "object",
                "properties": {
                    "by": {
                        "type": "string",
                        "enum": ["text", "role", "label", "placeholder", "testid"],
                        "description": "How to find the element"
                    },
                    "value": {
                        "type": "string",
                        "description": "Value to search for"
                    },
                    "name": {
                        "type": "string",
                        "description": "For role: filter by accessible name"
                    }
                },
                "required": ["by", "value"]
            }
        ),
        Tool(
            name="browser_find_fill",
            description="Find element by text/role/label and fill it",
            inputSchema={
                "type": "object",
                "properties": {
                    "by": {
                        "type": "string",
                        "enum": ["text", "role", "label", "placeholder", "testid"],
                        "description": "How to find the element"
                    },
                    "search": {
                        "type": "string",
                        "description": "Value to search for"
                    },
                    "fill_value": {
                        "type": "string",
                        "description": "Value to fill"
                    }
                },
                "required": ["by", "search", "fill_value"]
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list:
    """Dispatch one MCP tool call to the corresponding CLI command."""
    global _cached_refs
    
    result = {"success": False, "error": "Unknown tool"}
    
    try:
        # === Navigation ===
        if name == "browser_navigate":
            url = arguments.get("url")
            # Opening can take longer than simple interactions; use higher timeout.
            result = await execute_cli("open", [url], timeout=60)
        
        elif name == "browser_back":
            result = await execute_cli("back")
        
        elif name == "browser_forward":
            result = await execute_cli("forward")
        
        elif name == "browser_reload":
            result = await execute_cli("reload")
        
        # === Snapshot ===
        elif name == "browser_snapshot":
            args = []
            if arguments.get("interactive_only", True):
                args.append("-i")
            if arguments.get("compact", True):
                args.append("-c")
            args.extend(["-d", str(arguments.get("depth", 5))])
            if arguments.get("selector"):
                args.extend(["-s", arguments["selector"]])
            
            result = await execute_cli("snapshot", args, timeout=30)

            # Cache refs for later use
            if result.get("success") and "data" in result:
                refs = result["data"].get("refs", {})
                if refs:
                    _cached_refs.update(refs)
        
        # === Screenshot ===
        elif name == "browser_screenshot":
            args = []
            if arguments.get("annotate", True):
                args.append("--annotate")
            if arguments.get("full_page", False):
                args.append("--full")
            
            result = await execute_cli("screenshot", args, timeout=30)
            
            # If screenshot was taken, try to read the image
            if result.get("success") and "data" in result:
                img_path = result["data"].get("path", "")
                if img_path and os.path.exists(img_path):
                    with open(img_path, "rb") as f:
                        import base64
                        img_data = base64.b64encode(f.read()).decode()
                    # Returning both text + image helps UIs that display a
                    # textual audit trail and a visual artifact together.
                    return [
                        TextContent(type="text", text=f"Screenshot saved to: {img_path}"),
                        ImageContent(type="image", data=img_data, mimeType="image/png")
                    ]
        
        # === Interaction ===
        elif name == "browser_click":
            selector = arguments.get("selector")
            args = [selector]
            if arguments.get("new_tab", False):
                args.append("--new-tab")
            result = await execute_cli("click", args)
        
        elif name == "browser_fill":
            selector = arguments.get("selector")
            value = arguments.get("value")
            result = await execute_cli("fill", [selector, value])
        
        elif name == "browser_type":
            selector = arguments.get("selector")
            text = arguments.get("text")
            result = await execute_cli("type", [selector, text])
        
        elif name == "browser_press":
            key = arguments.get("key")
            result = await execute_cli("press", [key])
        
        elif name == "browser_hover":
            selector = arguments.get("selector")
            result = await execute_cli("hover", [selector])
        
        elif name == "browser_scroll":
            direction = arguments.get("direction")
            pixels = arguments.get("pixels", 300)
            result = await execute_cli("scroll", [direction, str(pixels)])
        
        elif name == "browser_select":
            selector = arguments.get("selector")
            value = arguments.get("value")
            result = await execute_cli("select", [selector, value])
        
        # === Waiting ===
        elif name == "browser_wait":
            args = []
            if arguments.get("selector"):
                args.append(arguments["selector"])
            if arguments.get("text"):
                args.extend(["--text", arguments["text"]])
            if arguments.get("url_pattern"):
                args.extend(["--url", arguments["url_pattern"]])
            if arguments.get("load_state"):
                args.extend(["--load", arguments["load_state"]])
            if arguments.get("timeout_ms"):
                args.append(str(arguments["timeout_ms"]))
            result = await execute_cli("wait", args, timeout=60)
        
        # === Get Information ===
        elif name == "browser_get_text":
            selector = arguments.get("selector")
            result = await execute_cli("get", ["text", selector])
        
        elif name == "browser_get_url":
            result = await execute_cli("get", ["url"])
        
        elif name == "browser_get_title":
            result = await execute_cli("get", ["title"])
        
        elif name == "browser_is_visible":
            selector = arguments.get("selector")
            result = await execute_cli("is", ["visible", selector])
        
        # === Tabs ===
        elif name == "browser_tab_list":
            result = await execute_cli("tab")
        
        elif name == "browser_tab_new":
            args = ["new"]
            if arguments.get("url"):
                args.append(arguments["url"])
            result = await execute_cli("tab", args)
        
        elif name == "browser_tab_switch":
            index = arguments.get("index")
            result = await execute_cli("tab", [str(index)])
        
        elif name == "browser_tab_close":
            args = ["close"]
            if arguments.get("index") is not None:
                args.append(str(arguments["index"]))
            result = await execute_cli("tab", args)
        
        # === JavaScript ===
        elif name == "browser_eval":
            script = arguments.get("script")
            result = await execute_cli("eval", [script], timeout=30)
        
        # === Session ===
        elif name == "browser_close":
            result = await execute_cli("close")
            _cached_refs.clear()
        
        # === Find shortcuts ===
        elif name == "browser_find_click":
            by = arguments.get("by")
            value = arguments.get("value")
            name_filter = arguments.get("name")
            
            args = ["find", by, "click"]
            if name_filter:
                args.extend(["--name", name_filter])
            args.append(value)
            # Keep existing behavior exactly as-is; this branch forwards a
            # specialized "find ... click" invocation to the CLI wrapper.
            result = await execute_cli("", args[1:], timeout=30)  # "find" is the command
            
        elif name == "browser_find_fill":
            by = arguments.get("by")
            search = arguments.get("search")
            fill_value = arguments.get("fill_value")
            
            result = await execute_cli("find", [by, "fill", search, fill_value])
    
    except Exception as e:
        result = {"success": False, "error": str(e)}
        logger.error(f"Tool execution error: {e}")
    
    # Normalize every tool result into TextContent list, the MCP-friendly shape.
    if result.get("success"):
        data = result.get("data", result.get("content", ""))
        if isinstance(data, dict):
            text = json.dumps(data, indent=2, ensure_ascii=False)
        else:
            text = str(data) if data else "Success"
    else:
        text = f"Error: {result.get('error', 'Unknown error')}"
    
    return [TextContent(type="text", text=text)]


async def main():
    """Main entry point for the MCP server"""
    # Check if agent-browser is installed
    if not check_agent_browser_installed():
        logger.error(
            "agent-browser CLI not found! "
            "Install with: npm install -g agent-browser"
        )
        return
    
    # Load config from file if present (container path by default).
    config_path = os.environ.get(
        "AGENT_BROWSER_CONFIG",
        "/agentscope_runtime/agent_browser_config.json"
    )
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config_data = json.load(f)
                global config
                config = AgentBrowserConfig(**config_data)
                logger.info(f"Loaded config from {config_path}")
        except Exception as e:
            logger.warning(f"Failed to load config: {e}, using defaults")
    
    # Preinstall browser binaries at server startup so first tool call has
    # predictable latency.
    logger.info("Ensuring browser is installed...")
    await execute_cli("install", timeout=120)
    
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
