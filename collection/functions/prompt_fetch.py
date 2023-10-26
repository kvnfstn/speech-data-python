from firebase_helper import getPromptsCollectionRef
from google.cloud.firestore_v1.field_path import FieldPath
import random

async def getNextPrompt(usedPrompts):
    try:
        prompts_col_ref = getPromptsCollectionRef()

        if len(usedPrompts) > 2:
            start_at = {FieldPath.document_id(): random.choice(usedPrompts)}
            #? doc says it can't be "not-in" but looking into it there is no limitation to it and it seems it can effectively be used
            unused_prompts_query_1 = prompts_col_ref.order_by(FieldPath.document_id(), direction='ASCENDING').start_at(start_at).where(FieldPath.document_id(), "not-in", usedPrompts).limit(1)
            unused_prompts_query_2 = prompts_col_ref.order_by(FieldPath.document_id(), direction='DESCENDING').start_at(start_at).where(FieldPath.document_id(), "not-in", usedPrompts).limit(1)
        else:
            random_dummy_doc = prompts_col_ref.document()
            unused_prompts_query_1 = prompts_col_ref.order_by(FieldPath.document_id(), direction='ASCENDING').where(FieldPath.document_id(), "<=", random_dummy_doc.id).where(FieldPath.document_id(), "not-in", usedPrompts).limit(1)
            unused_prompts_query_2 = prompts_col_ref.order_by(FieldPath.document_id(), direction='DESCENDING').where(FieldPath.document_id(), "<=", random_dummy_doc.id).where(FieldPath.document_id(), "not-in", usedPrompts).limit(1)
            await random_dummy_doc.delete()

        suitable_prompts = [p async for p in unused_prompts_query_1.stream()]

        if not suitable_prompts:
            suitable_prompts = [p async for p in unused_prompts_query_2.stream()]

        if suitable_prompts:
            random_prompt = suitable_prompts[0]
            prompt_as_dict = random_prompt.to_dict()
            if prompt_as_dict is not None:
                return {
                    **prompt_as_dict,
                    'id': random_prompt.id,
                    'position': len(usedPrompts) + 1
                }
            else:
                raise
        else:
            print("All available prompts have been seen by this user. Please add more to continue")
            raise Exception('NoMorePromptError')
    except Exception as e:
        raise e