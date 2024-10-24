from typing import Annotated, Literal

from fastapi import FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse


app = FastAPI(
    title="Basal Energy Expenditure Tool",
    description="Calculates Basal Energy Expenditure (BEE) and Total Daily Energy Expenditure (TDEE) based on user inputs.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class BEEFormInput(BaseModel):
    """
    Form-based input schema for calculating Basal Energy Expenditure (BEE) and Total Daily Energy Expenditure (TDEE).
    """

    unit_system: Literal["metric", "imperial"] = Field(
        default="metric",
        title="Unit System",
        examples=["metric"],
        description=(
            "Select your measurement system.\n\n"
            "- **Metric**: Use kilograms for weight and centimeters for height.\n"
            "- **Imperial**: Use pounds for weight and inches for height."
        ),
    )
    age: int = Field(
        title="Age",
        ge=1,
        le=150,
        examples=[25],
        description="Enter your age. Must be a value between 1 and 150.",
    )
    biological_sex: Literal["male", "female", "intersex"] = Field(
        title="Biological Sex",
        examples=["male"],
        description="Select your biological sex.",
    )
    weight: float = Field(
        title="Weight",
        ge=1.0,
        examples=[70.5],
        description=(
            "Enter your weight in kilograms (metric) or pounds (imperial). Must be a positive value."
        ),
    )
    height: float = Field(
        title="Height",
        ge=1.0,
        examples=[175.0],
        description=(
            "Enter your height in centimeters (metric) or inches (imperial). Must be a positive value."
        ),
    )
    activity_level: Literal[
        "sedentary",
        "lightly_active",
        "moderately_active",
        "very_active",
        "super_active"
    ] = Field(
        title="Activity Level",
        examples=["moderately_active"],
        description=(
            "Select your activity level.\n\n"
            "- **Sedentary**: Little to no exercise\n"
            "- **Lightly Active**: Light exercise (1-3 days per week)\n"
            "- **Moderately Active**: Moderate exercise (3–5 days per week)\n"
            "- **Very Active**: Heavy exercise (6–7 days per week)\n"
            "- **Super Active**: Very heavy exercise (twice per day, extra heavy workouts)"
        ),
    )


class BEEFormOutput(BaseModel):
    """
    Form-based output schema for Basal Energy Expenditure (BEE) and Total Daily Energy Expenditure (TDEE).
    """

    bee_kcal: float = Field(
        title="Basal Energy Expenditure (BEE) in kcal/day",
        examples=[1650.0],
        description="Your calculated Basal Energy Expenditure (BEE) in kilocalories per day.",
        format="display",
    )
    bee_kj: float = Field(
        title="Basal Energy Expenditure (BEE) in kJ/day",
        examples=[6908.6],
        description="Your calculated Basal Energy Expenditure (BEE) in kilojoules per day.",
        format="display",
    )
    tdee_kcal: float = Field(
        title="Total Daily Energy Expenditure (TDEE) in kcal/day",
        examples=[2000.0],
        description="Your calculated Total Daily Energy Expenditure (TDEE) based on your activity level, in kilocalories per day.",
        format="display",
    )
    tdee_kj: float = Field(
        title="Total Daily Energy Expenditure (TDEE) in kJ/day",
        examples=[8370.0],
        description="Your calculated Total Daily Energy Expenditure (TDEE) based on your activity level, in kilojoules per day.",
        format="display",
    )
    activity_factor: float = Field(
        title="Activity Factor",
        examples=[1.55],
        description="The activity factor used to calculate your TDEE.",
        format="display",
    )


@app.post(
    "/calculate_bee/",
    response_model=BEEFormOutput,
    summary="Calculate Basal and Total Daily Energy Expenditure",
    description="Calculate Basal Energy Expenditure (BEE) and Total Daily Energy Expenditure (TDEE) based on age, weight, height, biological sex, and activity level.",
)
def calculate_bee(
    data: Annotated[BEEFormInput, Form()],
) -> BEEFormOutput:
    """Calculate Basal Energy Expenditure (BEE) and Total Daily Energy Expenditure (TDEE).

    Args:
        data: BEEFormInput - Input data for calculating BEE and TDEE.

    Returns:
        BEEFormOutput: The calculated BEE and TDEE values.
    """
    # Unit conversion factors
    conversion_factors = {
        "metric": {"weight": 1.0, "height": 1.0},
        "imperial": {"weight": 0.453592, "height": 2.54},
    }

    unit = data.unit_system.lower()
    if unit not in conversion_factors:
        raise HTTPException(
            status_code=400,
            detail="Invalid unit system. Must be 'metric' or 'imperial'.",
        )

    factors = conversion_factors[unit]
    weight_in_kg = data.weight * factors["weight"]
    height_in_cm = data.height * factors["height"]

    # Calculate BEE using the Harris-Benedict equation
    if data.biological_sex.lower() == "male":
        bee = (
            66.473
            + (13.7516 * weight_in_kg)
            + (5.0033 * height_in_cm)
            - (6.7550 * data.age)
        )
    elif data.biological_sex.lower() in ["female", "intersex"]:
        bee = (
            655.0955
            + (9.5634 * weight_in_kg)
            + (1.8496 * height_in_cm)
            - (4.6756 * data.age)
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid biological sex. Must be 'male', 'female', or 'intersex'.",
        )

    # Determine activity factor
    activity_factors = {
        "sedentary": 1.2,
        "lightly_active": 1.375,
        "moderately_active": 1.55,
        "very_active": 1.725,
        "super_active": 1.9,
    }

    # Replace spaces with underscores for key matching
    activity_level_key = data.activity_level.lower().replace(" ", "_")
    multiplier = activity_factors.get(activity_level_key, 1.2)

    # Calculate Total Daily Energy Expenditure (TDEE)
    tdee = bee * multiplier

    # Convert kcal/day to kJ/day
    bee_kj = bee * 4.184
    tdee_kj = tdee * 4.184

    # Round the results to two decimal places
    bee = round(bee, 2)
    bee_kj = round(bee_kj, 2)
    tdee = round(tdee, 2)
    tdee_kj = round(tdee_kj, 2)

    return BEEFormOutput(
        bee_kcal=bee,
        bee_kj=bee_kj,
        tdee_kcal=tdee,
        tdee_kj=tdee_kj,
        activity_factor=multiplier,
    )


@app.get("/health", response_class=JSONResponse)
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "Application is running."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)