import boto3

def extract_text_from_pdf(bucket_name, document_name):
    session = boto3.Session(profile_name='cpisb_IsbUsersPS-962448382783')
    textract = session.client('textract', region_name='us-west-2')

    response = textract.analyze_document(
        Document={'S3Object': {'Bucket': bucket_name, 'Name': document_name}},
        FeatureTypes=["FORMS"]
    )

    blocks_map = {block['Id']: block for block in response['Blocks']}
    fields = {}

    for block in response['Blocks']:
        if block['BlockType'] == 'KEY_VALUE_SET' and 'KEY' in block.get('EntityTypes', []):
            key = extract_text(block, blocks_map)
            value = ''
            for rel in block.get('Relationships', []):
                if rel['Type'] == 'VALUE':
                    value_block = blocks_map.get(rel['Ids'][0])
                    value = extract_text(value_block, blocks_map)
            fields[key] = value

    return fields

def extract_text(block, blocks_map):
    text = ''
    if 'Relationships' in block:
        for rel in block['Relationships']:
            if rel['Type'] == 'CHILD':
                for child_id in rel['Ids']:
                    word = blocks_map[child_id]
                    if word['BlockType'] == 'WORD':
                        text += word['Text'] + ' '
                    elif word['BlockType'] == 'SELECTION_ELEMENT':
                        if word['SelectionStatus'] == 'SELECTED':
                            text += '✔ '
    return text.strip()
