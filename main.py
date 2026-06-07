from app.intent_extractor.extractor import extract_intent
from app.system_designer.designer import design_system
from app.schema_generator.generator import generate_schema
from app.validator.validator import validate_schema
from app.validator.validator import validate_schema
from app.repair_engine.repair import repair_schema

user_input = input("Enter App Idea: ")

intent = extract_intent(user_input)

print("\nINTENT:\n")
print(intent)

architecture = design_system(intent)

print("\nSYSTEM DESIGN:\n")
print(architecture)

schema = generate_schema(architecture)

print("\nGENERATED SCHEMA:\n")
print(schema)


validation = validate_schema(schema)

print("\nVALIDATION RESULT:\n")
print(validation)

validation = validate_schema(schema)

print("\nVALIDATION RESULT:\n")
print(validation)

repaired_schema = repair_schema(
    schema,
    validation
)

print("\nREPAIRED SCHEMA:\n")
print(repaired_schema)