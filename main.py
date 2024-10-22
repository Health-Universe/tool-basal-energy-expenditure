from typing import Annotated, Literal

from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import Field, BaseModel

app = FastAPI(
    title="Basal Energy Expenditure",
    description="Calculates daily energy expenditure.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class BEEFormInput(BaseModel):
    """
    Form-based input schema for calculating Basal Energy Expenditure (BEE) and Total Daily Energy Expenditure (TDEE).
    """

    age: int = Field(
        title="Age",
        ge=1,
        le=150,
        example=25,
        description="Enter your age. Must be a value between 1 and 150.",
    )
    biological_sex: Literal["male", "female", "intersex"] = Field(
        title="Biological Sex",
        example="male",
        description="Select your biological sex.",
    )
    weight: float = Field(
        title="Weight",
        ge=1.0,
        example=70.5,
        description="Enter your weight in kilograms. Must be a positive value.",
    )
    height: float = Field(
        title="Height",
        ge=1.0,
        example=175.0,
        description="Enter your height in centimeters. Must be a positive value.",
    )
    activity_level: Literal[
        "sedentary", "lightly active", "moderately active", "very active", "super active"
    ] = Field(
        title="Activity Level",
        example="moderately active",
        description="Select your activity level. Options: sedentary, lightly active, moderately active, very active, super active.",
    )


class BEEFormOutput(BaseModel):
    """
    Form-based output schema for Basal Energy Expenditure (BEE) and Total Daily Energy Expenditure (TDEE).
    """

    bee_kcal: float = Field(
        title="Basal Energy Expenditure (BEE) in kcal/day",
        example=1650.0,
        description="Your calculated Basal Energy Expenditure (BEE) in kilocalories per day.",
        format="display",
    )
    bee_kj: float = Field(
        title="Basal Energy Expenditure (BEE) in kJ/day",
        example=6908.6,
        description="Your calculated Basal Energy Expenditure (BEE) in kilojoules per day.",
        format="display",
    )
    tdee_kcal: float = Field(
        title="Total Daily Energy Expenditure (TDEE) in kcal/day",
        example=2000.0,
        description="Your calculated Total Daily Energy Expenditure (TDEE) based on your activity level, in kilocalories per day.",
        format="display",
    )
    tdee_kj: float = Field(
        title="Total Daily Energy Expenditure (TDEE) in kJ/day",
        example=8370.0,
        description="Your calculated Total Daily Energy Expenditure (TDEE) based on your activity level, in kilojoules per day.",
        format="display",
    )
    activity_factor: float = Field(
        title="Activity Factor",
        example=1.55,
        description="The activity factor used to calculate your TDEE.",
        format="display",
    )


@app.post(
    "/calculate_bee/",
    response_model=BEEFormOutput,
)
def calculate_bee(
        data: Annotated[BEEFormInput, Form()],
) -> BEEFormOutput:
    """Calculate Basal Energy Expenditure (BEE) and Total Daily Energy Expenditure (TDEE).

    Args:
        data: Annotated[BEEFormInput, Form()]: Input data for calculating BEE and TDEE.

    Returns:
        BEEFormOutput: The calculated BEE and TDEE values.

    """
    # Calculate BEE using the Harris-Benedict equation
    if data.biological_sex.lower() == "male":
        bee = (
                66.473
                + (13.7516 * data.weight)
                + (5.0033 * data.height)
                - (6.7550 * data.age)
        )
    else:
        bee = (
                655.0955
                + (9.5634 * data.weight)
                + (1.8496 * data.height)
                - (4.6756 * data.age)
        )

        # Determine activity factor
    activity_factors = {
        "sedentary": 1.2,
        "lightly active": 1.375,
        "moderately active": 1.55,
        "very active": 1.725,
        "super active": 1.9,
    }
    activity_factor = activity_factors.get(data.activity_level.lower(), 1.2)

    # Calculate Total Daily Energy Expenditure (TDEE)
    tdee = bee * activity_factor

    # Convert kcal/day to kJ/day
    bee_kj = bee * 4.184
    tdee_kj = tdee * 4.184

    return BEEFormOutput(
        bee_kcal=bee,
        bee_kj=bee_kj,
        tdee_kcal=tdee,
        tdee_kj=tdee_kj,
        activity_factor=activity_factor,
    )
