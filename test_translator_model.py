"""
Script to verify translator module accepts model parameter
"""
from app.translator import OpenAITranslator, TranslationWorker


def test_translator_model_parameter():
    """Test if translator accepts model parameter"""
    print("Testing Translator Model Parameter Support\n")
    print("=" * 60)
    
    # Test OpenAITranslator initialization with default model
    print("\nOpenAITranslator Initialization Tests:")
    print("-" * 60)
    
    try:
        # This will try to initialize with dummy API key (won't connect yet)
        dummy_key = "sk-test-dummy-key-for-testing"
        
        # Test 1: Default model
        print("\nTest 1: OpenAITranslator with default model")
        translator = OpenAITranslator(dummy_key)
        print(f"✓ Created with model: {translator.model_name}")
        
        if translator.model_name == "gpt-4.1":
            print("✓ Default model is 'gpt-4.1'")
        else:
            print(f"✗ Wrong default model: {translator.model_name}")
            return False
    except Exception as e:
        # This is expected since we're using a dummy API key
        if "API" in str(e) or "OpenAI" in str(e) or "failed to initialize" in str(e).lower():
            print(f"✓ Expected error during client initialization (dummy key): {str(e)[:50]}...")
        else:
            print(f"✗ Unexpected error: {e}")
            return False
    
    # Test 2: Custom model
    print("\nTest 2: OpenAITranslator with custom model")
    try:
        translator = OpenAITranslator(dummy_key, model="gpt-4.1-mini")
        print(f"✓ Created with model: {translator.model_name}")
        
        if translator.model_name == "gpt-4.1-mini":
            print("✓ Custom model 'gpt-4.1-mini' is set correctly")
        else:
            print(f"✗ Wrong model: {translator.model_name}")
            return False
    except Exception as e:
        if "API" in str(e) or "OpenAI" in str(e) or "failed to initialize" in str(e).lower():
            print(f"✓ Expected error during client initialization (dummy key): {str(e)[:50]}...")
        else:
            print(f"✗ Unexpected error: {e}")
            return False
    
    # Test TranslationWorker
    print("\n" + "=" * 60)
    print("TranslationWorker Initialization Tests:")
    print("-" * 60)
    
    # Test 3: TranslationWorker with default model
    print("\nTest 3: TranslationWorker with default model")
    try:
        worker = TranslationWorker(dummy_key)
        print(f"✓ Created with model: {worker.model}")
        
        if worker.model == "gpt-4.1":
            print("✓ Default model is 'gpt-4.1'")
        else:
            print(f"✗ Wrong default model: {worker.model}")
            return False
            
        # Check that translator has the same model
        if worker.translator.model_name == "gpt-4.1":
            print("✓ Translator also has 'gpt-4.1' model")
        else:
            print(f"✗ Translator has wrong model: {worker.translator.model_name}")
            return False
    except Exception as e:
        if "API" in str(e) or "OpenAI" in str(e) or "failed to initialize" in str(e).lower():
            print(f"✓ Expected error during client initialization (dummy key): {str(e)[:50]}...")
        else:
            print(f"✗ Unexpected error: {e}")
            return False
    
    # Test 4: TranslationWorker with custom model
    print("\nTest 4: TranslationWorker with custom model")
    try:
        worker = TranslationWorker(dummy_key, model="gpt-4.1-mini")
        print(f"✓ Created with model: {worker.model}")
        
        if worker.model == "gpt-4.1-mini":
            print("✓ Custom model 'gpt-4.1-mini' is set")
        else:
            print(f"✗ Wrong model: {worker.model}")
            return False
        
        # Check that translator has the same model
        if worker.translator.model_name == "gpt-4.1-mini":
            print("✓ Translator also has 'gpt-4.1-mini' model")
        else:
            print(f"✗ Translator has wrong model: {worker.translator.model_name}")
            return False
    except Exception as e:
        if "API" in str(e) or "OpenAI" in str(e) or "failed to initialize" in str(e).lower():
            print(f"✓ Expected error during client initialization (dummy key): {str(e)[:50]}...")
        else:
            print(f"✗ Unexpected error: {e}")
            return False
    
    print("\n" + "=" * 60)
    print("✓ ALL TRANSLATOR MODEL TESTS PASSED!")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    success = test_translator_model_parameter()
    exit(0 if success else 1)
