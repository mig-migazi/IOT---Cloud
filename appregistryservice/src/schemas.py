from marshmallow import Schema, fields, validate, ValidationError

class ApplicationRegistrationSchema(Schema):
    """Schema for application registration"""
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str(allow_none=True)
    version = fields.Str(required=True, validate=validate.Length(min=1, max=20))
    developer = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    contact_email = fields.Email(required=True)
    category = fields.Str(allow_none=True, validate=validate.Length(max=50))
    platform = fields.Str(
        allow_none=True, 
        validate=validate.OneOf(['web', 'mobile', 'desktop', 'api'])
    )
    devicetypes = fields.List(fields.Str(), allow_none=True, missing=list)

class ApplicationUpdateSchema(Schema):
    """Schema for application updates"""
    name = fields.Str(validate=validate.Length(min=1, max=100))
    description = fields.Str(allow_none=True)
    version = fields.Str(validate=validate.Length(min=1, max=20))
    developer = fields.Str(validate=validate.Length(min=1, max=100))
    contact_email = fields.Email()
    category = fields.Str(allow_none=True, validate=validate.Length(max=50))
    platform = fields.Str(
        allow_none=True, 
        validate=validate.OneOf(['web', 'mobile', 'desktop', 'api'])
    )
    devicetypes = fields.List(fields.Str(), allow_none=True, missing=list)
    status = fields.Str(
        allow_none=True,
        validate=validate.OneOf(['active', 'inactive', 'pending'])
    )

class ApplicationResponseSchema(Schema):
    """Schema for application response"""
    id = fields.Str()
    name = fields.Str()
    description = fields.Str()
    version = fields.Str()
    developer = fields.Str()
    contact_email = fields.Email()
    category = fields.Str()
    platform = fields.Str()
    devicetypes = fields.List(fields.Str())
    status = fields.Str()
    api_key = fields.Str()
    created_at = fields.Str()
    updated_at = fields.Str()
