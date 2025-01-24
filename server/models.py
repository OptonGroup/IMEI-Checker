from pydantic import BaseModel, Field, validator

class PhoneInfo(BaseModel):
    imei: str = Field(..., description="IMEI number of the phone")

    @validator('imei')
    def validate_imei(cls, value):
        value = value.strip()
        
        if not value:
            raise ValueError("IMEI cannot be empty")
        
        if not value.isdigit():
            raise ValueError("IMEI must contain only digits")
            
        if len(value) != 15:
            raise ValueError(f"IMEI must be exactly 15 digits long, got {len(value)} digits")
            
        sum = 0
        double = False
        for digit in reversed(value):
            d = int(digit)
            if double:
                d *= 2
                if d > 9:
                    d -= 9
            sum += d
            double = not double
            
        if sum % 10 != 0:
            raise ValueError("Invalid IMEI checksum")
            
        return value