from mcp.server.fastmcp import FastMCP
import asyncio

mcp = FastMCP("test")
skills = ["skillA", "skillB"]

for skill in skills:
    @mcp.resource(f"skills://{skill}/SKILL.md")
    def get_skill_md() -> str:
        return f"Content of {skill}"

async def main():
    resources = await mcp.list_resources()
    print("Resources:", [r.uri for r in resources])
    for r in resources:
        content = await mcp.read_resource(r.uri)
        print(f"Read {r.uri}: {content}")

asyncio.run(main())
