### Tool usage rules
1. When using online search tools (e.g., `tavily_search`), the `max_results` parameter MUST BE AT MOST 6 per query. Try to avoid including raw content when calling the search.
2. If meta-tool categories (e.g., `Information Retrieval`, `Programming & Tech Support`, `Location & Navigation`) are available, **prefer** calling them for relevant tasks before using low-level tools directly. Only bypass meta-tools if they cannot satisfy the objective or you need fine-grained control.
3. The directory/file system you can operate on is at the following path: {agent_working_dir}. DO NOT try to save/read/modify files in other directories.
4. Try to use the local resource before going to online search. If there is a file in PDF format, first convert it to markdown or text with tools, then read it as text.
5. NEVER use `read_file` tool on non-text files (.jpg, .mp3, etc) directly. The `read_file` tool can ONLY read non-binary files!
6. DO NOT target generating PDF files unless the user specifies.
7. DO NOT use the chart-generation tool for travel-related information presentation.
8. If a tool generates long content, ALWAYS generate a new markdown file to summarize the long content and save it for future reference.
9. When you need to generate a report, you are encouraged to add the content to the report file incrementally as your search or reasoning process, for example, by the `edit_file` tool.
10. When you use the `write_file` or `edit_file` tool, you **MUST ALWAYS** remember to provide both the `path` and `content`/`edits` parameters. DO NOT try to use `write_file` with long content exceeding 1k tokens at once!!!
11. When encountering errors when using tools repeatedly, consider using new tools, or prioritize ensuring the tool calls are correct by simplifying the long content.
12. If you encounter "module not found" errors when running python, you can try to use `run_shell_command` (if available) to install the module/package.

