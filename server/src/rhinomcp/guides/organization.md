# Model organization

Use a meaningful assembly root with functional children, for example
Assembly::Frame::Left and Assembly::Panels. Create parents before their children
with create_layer(name=..., parent=...). When names repeat, use exact full paths for
parent references; an ambiguous short name is not a reliable identifier.

Assign objects with update_object_attributes(id=..., layer=...). modify_object does
not accept a layer argument. Inspect assignments with get_object_attributes.
Meaningful object names complement layers; they do not replace them. Keep temporary
profiles and cutters distinct from final parts, and preserve existing user layers.

Verify both the layer hierarchy and object membership. A correctly named layer is
not proof that the intended objects are on it. Where saved organization matters,
check the reopened file, including visibility and unintended objects on Default.
