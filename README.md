# Use Genesis API
Sample Code to use the Destatis API to pull data

## CF DynamoDb Stack

→ the stack-create Command (CLI)

```bash
aws cloudformation create-stack \
--profile default \
--stack-name dynamodb-stack \
--template-body file://global_dynamodb.yaml
```

→ here the stack-update command (CLI)

```bash
aws cloudformation update-stack \
--profile default \
--stack-name dynamodb-stack \
--template-body file://global_dynamodb.yaml
```
