from endee import Endee

# Connect to Endee server
client = Endee()
client.set_base_url("http://localhost:8080/api/v1")

# List all existing indexes
existing_indexes = client.list_indexes()
print("Existing indexes:", existing_indexes)

# Delete all indexes
for idx in existing_indexes:
    client.delete_index(idx)
    print(f"Deleted index: {idx}")

print("✅ All indexes removed. You can now start fresh.")
