"""
Complete workflow example showing all ROMA-VLM capabilities.

This example demonstrates:
1. Single image analysis
2. Multi-image comparison
3. Complex task decomposition
4. Custom VLM configuration per node
5. Verification
"""

import asyncio
from pathlib import Path
from roma_vlm import multimodal_solve


async def example_1_simple_analysis():
    """Example 1: Simple single image analysis."""
    print("\n" + "="*80)
    print("EXAMPLE 1: Simple Image Analysis")
    print("="*80)
    
    result = await multimodal_solve(
        goal="Describe this image in detail. What are the main subjects?",
        images="path/to/image.jpg",  # Replace with real path
        executor_model="openrouter/anthropic/claude-3-5-sonnet"
    )
    
    print(result)


async def example_2_comparison():
    """Example 2: Compare multiple images."""
    print("\n" + "="*80)
    print("EXAMPLE 2: Multi-Image Comparison")
    print("="*80)
    
    result = await multimodal_solve(
        goal="""
        Compare these three images:
        1. What do they have in common?
        2. What are the unique features of each?
        3. Which image is most visually striking and why?
        """,
        images=[
            "path/to/image1.jpg",
            "path/to/image2.jpg",
            "path/to/image3.jpg",
        ],
        verify=True
    )
    
    print(result)


async def example_3_complex_task():
    """Example 3: Complex multi-step visual task."""
    print("\n" + "="*80)
    print("EXAMPLE 3: Complex Multi-Step Task")
    print("="*80)
    
    result = await multimodal_solve(
        goal="""
        Analyze these product images and:
        
        Step 1: For each product image, extract:
        - Product type and category
        - Visible features and specifications
        - Estimated price range
        - Target audience
        
        Step 2: Compare all products:
        - Create feature comparison matrix
        - Identify best value proposition
        - Note quality indicators
        
        Step 3: Generate recommendation:
        - Rank products by value
        - Explain ranking rationale
        - Suggest ideal use case for each
        
        Present as structured report with sections.
        """,
        images=[
            "products/product1.jpg",
            "products/product2.jpg",
            "products/product3.jpg",
        ],
        # Custom VLM per stage
        atomizer_model="openrouter/google/gemini-2.0-flash-exp",
        planner_model="openrouter/openai/gpt-4o",
        executor_model="openrouter/anthropic/claude-3-5-sonnet",
        aggregator_model="openrouter/anthropic/claude-3-5-sonnet",
        verifier_model="openrouter/anthropic/claude-3-5-sonnet",
        # Custom configs
        executor_config={"temperature": 0.4},  # Lower for factual extraction
        aggregator_config={"temperature": 0.6},  # Slightly higher for synthesis
        max_depth=4,
        verify=True
    )
    
    print(result)


async def example_4_document_processing():
    """Example 4: Document OCR and data extraction."""
    print("\n" + "="*80)
    print("EXAMPLE 4: Document Processing")
    print("="*80)
    
    result = await multimodal_solve(
        goal="""
        Process these invoice images:
        
        1. Extract structured data from each invoice:
           - Invoice number and date
           - Vendor information
           - Line items (description, quantity, price)
           - Totals (subtotal, tax, grand total)
        
        2. Validate data:
           - Check math calculations
           - Flag missing information
           - Note any inconsistencies
        
        3. Aggregate:
           - Total spent across all invoices
           - Most frequent vendor
           - Category breakdown
        
        Output as JSON for easy parsing.
        """,
        images=[
            "invoices/invoice_001.jpg",
            "invoices/invoice_002.jpg",
            "invoices/invoice_003.jpg",
        ],
        executor_model="openrouter/anthropic/claude-3-5-sonnet",
        executor_config={
            "temperature": 0.2,  # Very low for accuracy
            "max_tokens": 4096
        },
        verify=True
    )
    
    print(result)


async def example_5_medical_imaging():
    """Example 5: Medical image analysis (educational)."""
    print("\n" + "="*80)
    print("EXAMPLE 5: Medical Image Analysis (Educational Only)")
    print("="*80)
    
    result = await multimodal_solve(
        goal="""
        EDUCATIONAL ANALYSIS - NOT FOR DIAGNOSIS
        
        Analyze these chest X-ray images:
        
        1. For each image:
           - Identify visible anatomical structures
           - Measure cardiothoracic ratio (CTR)
           - Note any visible abnormalities or patterns
           - Assess image quality and positioning
        
        2. Comparison:
           - Compare measurements across images
           - Note any changes or progression
           - Identify consistent vs. variable findings
        
        3. Summary:
           - Key observations
           - Measurements summary
           - Educational notes on findings
        
        IMPORTANT: Add disclaimer that this is educational only.
        Real diagnosis requires licensed radiologists.
        """,
        images=[
            "medical/xray_patient_2023.jpg",
            "medical/xray_patient_2024.jpg",
        ],
        executor_model="openrouter/anthropic/claude-3-5-sonnet",
        executor_config={
            "temperature": 0.3,  # Conservative for medical
            "max_tokens": 8192   # Detailed analysis
        },
        aggregator_config={
            "temperature": 0.4,
            "max_tokens": 8192
        },
        verifier_config={
            "temperature": 0.0   # Strict verification
        },
        max_depth=3,
        verify=True
    )
    
    print(result)
    print("\n⚠️  DISCLAIMER: Educational purposes only. Consult medical professionals.")


async def example_6_custom_workflow():
    """Example 6: Custom workflow with individual modules."""
    print("\n" + "="*80)
    print("EXAMPLE 6: Custom Workflow")
    print("="*80)
    
    from roma_vlm.modules import MultimodalExecutor, MultimodalAtomizer
    
    # Create modules
    atomizer = MultimodalAtomizer(
        model="openrouter/google/gemini-2.0-flash-exp",
        model_config={"temperature": 0.6}
    )
    
    executor = MultimodalExecutor(
        model="openrouter/anthropic/claude-3-5-sonnet",
        model_config={"temperature": 0.5}
    )
    
    goal = "Analyze architectural elements in these building photos"
    images = ["architecture/building1.jpg", "architecture/building2.jpg"]
    
    # Custom logic: check atomization first
    atomized = await atomizer.aforward(goal=goal, images=images)
    
    print(f"Is atomic: {atomized.is_atomic}")
    print(f"Node type: {atomized.node_type}")
    
    if atomized.is_atomic:
        print("\nExecuting directly...")
        result = await executor.aforward(goal=goal, images=images)
        print(result.output)
    else:
        print("\nNeeds planning - falling back to full solve...")
        result = await multimodal_solve(goal=goal, images=images)
        print(result)


async def run_all_examples():
    """Run all examples sequentially."""
    examples = [
        ("Simple Analysis", example_1_simple_analysis),
        ("Multi-Image Comparison", example_2_comparison),
        ("Complex Multi-Step", example_3_complex_task),
        ("Document Processing", example_4_document_processing),
        ("Medical Imaging", example_5_medical_imaging),
        ("Custom Workflow", example_6_custom_workflow),
    ]
    
    print("\n" + "="*80)
    print("ROMA-VLM COMPLETE WORKFLOW EXAMPLES")
    print("="*80)
    print("\nNote: Update image paths before running!")
    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    print("\n" + "="*80)
    
    # Run each example (comment out as needed)
    # await example_1_simple_analysis()
    # await example_2_comparison()
    # await example_3_complex_task()
    # await example_4_document_processing()
    # await example_5_medical_imaging()
    # await example_6_custom_workflow()
    
    print("\n" + "="*80)
    print("Examples complete!")
    print("="*80)


if __name__ == "__main__":
    # Run all examples
    asyncio.run(run_all_examples())
    
    # Or run individual example:
    # asyncio.run(example_1_simple_analysis())

