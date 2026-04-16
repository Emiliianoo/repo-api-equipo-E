from pydantic import BaseModel, Field
from typing import List

class BillingInfo(BaseModel):
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    email: str

class LineItem(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)

class RequestedOrder(BaseModel):
  payment_method: str = Field(min_length=1)
  payment_method_title: str = Field(min_length=1)
  set_paid: bool
  billing: BillingInfo
  line_items: List[LineItem] = Field(min_items=1)

  model_config = {
     "json_schema_extra": {
        "example": {
          "payment_method": "metodo de ejemplo",
          "payment_method_title": "titulo de ejemplo",
          "set_paid": True,
          "billing": {
              "first_name": "Nombre de ejemplo",
              "last_name": "Apellido de ejemplo",
              "email": "alguien@ejemplo.com"
              },
          "line_items": [{"product_id": 1, "quantity": 1}]
          }
      }
    }
