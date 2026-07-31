import asyncio
import os
from bo2_emblem.ai_hermes import HermesConfig, AIProvider, generate_emblem_async, EmblemConcept

async def main():
    print('Testing NVIDIA integration...')
    config = HermesConfig(
        provider=AIProvider.NVIDIA,
        endpoint='https://integrate.api.nvidia.com/v1',
        api_key=os.environ.get('NVIDIA_API_KEY', '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'),
        model='nvidia/nemotron-3-ultra-550b-a55b'
    )
    concept = EmblemConcept(
        name='AI Generated',
        description='an alien drinking soda',
        style='detailed',
        complexity=3,
        symmetry='bilateral'
    )
    try:
        plan = await generate_emblem_async(
            concept=concept,
            config=config
        )
        print(f'Success! Generated {len(plan.layers)} layers.')
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    asyncio.run(main())
