- Visual question answering
- Image captioning
- OCR on reciepts / invoices / handwritings
- Visual Search : Go find links for this image given in the prompt




    result = await multimodal_solve(
        goal="What objects can you see in this image? List them.",
        images="path/to/your/image.jpg",  # Replace with actual image path
    )


result = await multimodal_solve(
    goal="Process architectural blueprints",
    images=["floor1.png", "floor2.png"],
)


    result = await multimodal_solve(
        goal="Describe this image in detail. What are the main subjects?",
        images="path/to/image.jpg",  # Replace with real path
    )


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
    )


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
    )
    






    
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

    )













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

    )
















    goal = "Analyze architectural elements in these building photos"
    images = ["architecture/building1.jpg", "architecture/building2.jpg"]
    
















result = await multimodal_solve(
        goal="""
        Extract information from this invoice image:
        1. Invoice number and date
        2. Vendor name and contact
        3. All line items with quantities and prices
        4. Subtotal, tax, and total amounts
        5. Payment terms
        
        Format the output as structured JSON.
        """,
        images="path/to/invoice.jpg",
    )
    
    
    
result = await multimodal_solve(
        goal="""
        Process these filled forms:
        1. Extract all handwritten and typed text
        2. Identify form fields and their values
        3. Validate completeness (flag missing fields)
        4. Create a structured summary of all forms
        """,
        images=["path/to/form1.jpg","path/to/form2.jpg","path/to/form3.jpg"]
    )
    
    
   
    
result = await multimodal_solve(
        goal="""
        Process these receipts and:
        1. Extract merchant name, date, and total from each
        2. Categorize expenses (food, transport, supplies, etc.)
        3. Calculate total expenses by category
        4. Create expense report summary
        """,
        images=[
        "receipts/receipt1.jpg",
        "receipts/receipt2.jpg",
        "receipts/receipt3.jpg",
        "receipts/receipt4.jpg",
        "receipts/receipt5.jpg",
    ],
    )




# case 0
result = await multimodal_solve(
    goal="Analyze these X-rays and generate a diagnostic report",
    images=["xray1.jpg", "xray2.jpg"],
)



# case 1
result = await multimodal_solve(
    goal="What's in this image?",
    images="photo.jpg"
)

# case 2
result = await multimodal_solve(
    goal="What objects are in this image?",
    images="photo.jpg"
)


# case 3
result = await multimodal_solve(
    goal="""
    Analyze these medical charts:
    1. Extract vitals from each
    2. Identify abnormal trends
    3. Generate diagnostic summary
    """,
    images=["chart1.png", "chart2.png", "chart3.png"],
)



# case 4
result = await multimodal_solve(
    goal="Complex multi-step visual task",
    images=["img1.jpg", "img2.jpg"],
)


# case 5
result = await multimodal_solve(
    goal="Complex visual analysis task",
    images=["img1.jpg", "img2.jpg"],
)



# case 6
result = await multimodal_solve(
    goal="""
    Analyze this X-ray and identify:
    1. Anatomical structures
    2. Any visible abnormalities
    3. Measurements if possible
    """,
    images="xray.jpg",
)



# case 7
result = await multimodal_solve(
    goal="Describe this image in detail",
    images="photo.jpg"
)


# Case 8 : Multi-Image Comparison
result = await multimodal_solve(
    goal="Compare these images and find differences",
    images=["image1.jpg", "image2.jpg", "image3.jpg"]
)


# Case 9 : Document OCR
result = await multimodal_solve(
    goal="Extract all text from this document image",
    images="document.jpg",
)




# case 10
result = await multimodal_solve(
    goal="Compare these X-rays and identify changes",
    images=["xray_2023.jpg", "xray_2024.jpg"]
)



result = await multimodal_solve(
    goal='''
    Analyze these medical charts:
    1. Extract vitals from each chart
    2. Identify any abnormal trends
    3. Generate diagnostic summary
    ''',
    images=["chart1.png", "chart2.png", "chart3.png"],
)





    result = await multimodal_solve(
        goal="""
        Compare these images and:
        1. Identify common elements across all images
        2. Note unique features in each image
        3. Provide a comparative analysis
        """,
        images=["path/to/image1.jpg","path/to/image2.jpg","path/to/image3.jpg"],
    )




    result = await multimodal_solve(
        goal="""
        Analyze these chest X-rays and:
        1. Identify anatomical structures
        2. Measure cardiothoracic ratio if possible
        3. Note any visible abnormalities
        4. Compare findings across images
        5. Generate a structured radiology-style report
        
        IMPORTANT: This is for educational purposes only. 
        Real medical diagnosis requires licensed professionals.
        """,
        images=["path/to/xray_front.jpg","path/to/xray_side.jpg"],
    )





   patient_scans = {
        "patient_001": ["scans/p001_xray1.jpg", "scans/p001_xray2.jpg"],
        "patient_002": ["scans/p002_xray1.jpg", "scans/p002_xray2.jpg"],
        "patient_003": ["scans/p003_xray1.jpg", "scans/p003_xray2.jpg"],
    }
    
    results = {}
    
    for patient_id, scans in patient_scans.items():
        print(f"\nAnalyzing {patient_id}...")
        
        result = await multimodal_solve(
            goal=f"Analyze X-rays for {patient_id} and provide findings",
            images=scans,
            executor_model="openrouter/anthropic/claude-3-5-sonnet"
        )
        
        results[patient_id] = result
        print(f"✓ {patient_id} complete")




    
#     result = await multimodal_solve(
#         goal="Extract all text and numbers from this image using OCR",
#         images="imgs/calculator.png",
#     )
    

#     result = await multimodal_solve(
#         goal="Analyze this fitness/workout image and provide detailed observations",
#         images="imgs/workout.PNG",
#     )


#     result = await multimodal_solve(
#         goal="Use calculator tool to perform the calculation shown in the image",
#         images="imgs/calculator.png",
#     )

    
#     result = await multimodal_solve(
#         goal="Compare these images and identify what type of content each contains",
#         images=["imgs/calculator.png", "imgs/reciept.png"],
#     )


#     default_result = await multimodal_solve(
#         goal="Analyze this image in detail",
#         images="imgs/calculator.png",
#     )

#     custom_result = await multimodal_solve(
#         goal="Analyze this image in detail",
#         images="imgs/calculator.png",
#     )
    