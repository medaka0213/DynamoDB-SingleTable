#!/usr/bin/env python3
"""
Example script showing how to use apply_model_change_records with BaseModel instances.

This demonstrates the new function that can be imported and used directly
instead of having to go through the CLI with module paths.
"""

from ddb_single import Table, BaseModel, DBField, apply_model_change_records
import datetime


def main():
    # Create a test table
    table = Table(
        table_name="example_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
        endpoint_url="http://localhost:8000",  # Using DynamoDB Local
        region_name="us-west-2",
        aws_access_key_id="fakeMyKeyId",
        aws_secret_access_key="fakeSecretAccessKey",
    )
    table.init()

    # Define your models
    class User(BaseModel):
        __table__ = table
        __model_name__ = "user"
        name = DBField(unique_key=True)
        email = DBField(search_key=True)

    class Post(BaseModel):
        __table__ = table
        __model_name__ = "post"
        title = DBField(unique_key=True)
        content = DBField(search_key=True)

    # Now you can use apply_model_change_records directly with your model classes
    print("Applying model change records...")
    try:
        apply_model_change_records(table, [User, Post])
        print("✅ Successfully applied model change records!")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n" + "="*50)
    print("This is much easier than using the CLI which requires:")
    print("  python -m ddb_single.cli apply-model-change my_module")
    print("Now you can just import and use the function directly!")


if __name__ == "__main__":
    main()