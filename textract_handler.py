import boto3

def extract_text_from_pdf(bucket_name, document_name):
    # Use the correct profile from aws configure sso
    session = boto3.Session(profile_name='cpisb_IsbUsersPS-962448382783')
    textract = session.client('textract', region_name='us-west-2')

    response = textract.analyze_document(
        Document={'S3Object': {'Bucket': bucket_name, 'Name': document_name}},
        FeatureTypes=["FORMS"]
    )

    fields = {}
    for block in response['Blocks']:
        if block['BlockType'] == 'KEY_VALUE_SET' and 'KEY' in block.get('EntityTypes', []):
            key = ''
            value = ''
            for rel in block.get('Relationships', []):
                if rel['Type'] == 'VALUE':
                    value_block = next(b for b in response['Blocks'] if b['Id'] == rel['Ids'][0])
                    key = block['Text'] if 'Text' in block else ''
                    value = value_block['Text'] if 'Text' in value_block else ''
                    fields[key] = value

    return fields
