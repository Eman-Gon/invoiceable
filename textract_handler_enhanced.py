import boto3

def extract_with_textract(bucket, document):
    session = boto3.Session(profile_name="cpisb_IsbUsersPS-962448382783")
    client = session.client("textract", region_name="us-west-2")

    response = client.analyze_document(
        Document={"S3Object": {"Bucket": bucket, "Name": document}},
        FeatureTypes=["TABLES", "FORMS"]
    )

    lines = []
    for block in response["Blocks"]:
        if block["BlockType"] == "LINE":
            lines.append(block["Text"])

    return "\n".join(lines)
