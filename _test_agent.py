import asyncio
import uuid
from vanna_setup import agent
from vanna.core.user import RequestContext

async def test():
    req_ctx = RequestContext(
        headers={},
        cookies={},
        metadata={"request_id": str(uuid.uuid4())},
    )
    print("Sending message...")
    async for component in agent.send_message(req_ctx, "How many patients do we have?"):
        print("-------------")
        print("Component:", type(component))
        print("Dir:", dir(component))
        if component.rich_component:
            print("Rich Type:", type(component.rich_component))
            print("Rich Dir:", dir(component.rich_component))
            print("Rich Attrs:", vars(component.rich_component))
        if component.simple_component:
            print("Simple Attrs:", vars(component.simple_component))

if __name__ == "__main__":
    asyncio.run(test())
