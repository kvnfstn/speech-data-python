from firebase_helper import getPromptsCollectionRef
import random


async def getNextPrompt(usedPrompts):
    try:
        prompts_col_ref = getPromptsCollectionRef()
        #! this is stupid because it means to get a new prompt you will need to go through ALL existing prompts everytime ???
        #! considering you are billed by the # of retrieved references, this is not the way to go
        matching_prompts = [prompt async for prompt in prompts_col_ref.list_documents() if prompt not in usedPrompts]

        if matching_prompts:
            random_prompt = random.choice(matching_prompts)
            prompt_dict = random_prompt.get().to_dict()

            if prompt_dict is None:
                raise Exception("Doc Ref does not exist. This should NOT be happening.")
            
            return {
                **prompt_dict,
                'id': random_prompt.id,
                'position': len(usedPrompts) + 1
            }
        else:
            print(
                "All available prompts have been seen by this user. Please add more to continue")
            raise Exception('NoMorePromptError')
    except Exception as e:
        raise e
