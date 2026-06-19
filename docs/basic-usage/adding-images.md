---
title: Adding images
weight: 17
---

# Adding images

## Apple local images

Apple images are PNG files bundled into the `.pkpass` archive:

```python
builder.set_icon_image("/srv/app/icon.png", "/srv/app/icon@2x.png")
builder.set_logo_image("/srv/app/logo.png")
builder.set_strip_image("/srv/app/strip.png")
builder.set_thumbnail_image("/srv/app/thumb.png")
```

Each setter accepts optional `@2x` and `@3x` paths.

## Apple remote images

When images are already hosted on HTTPS, use the remote setters instead of copying files to disk first:

```python
builder.set_remote_logo_image("https://cdn.example.com/logo.png")
builder.set_remote_icon_image(
    "https://cdn.example.com/icon.png",
    "https://cdn.example.com/icon@2x.png",
)
builder.set_remote_strip_image("https://cdn.example.com/strip.png")
builder.set_remote_thumbnail_image("https://cdn.example.com/thumb.png")
```

Remote images are fetched when the `.pkpass` archive is generated. The stored `MobilePass.images` JSON records `is_remote: true` so hydrated builders can regenerate the pass later.

## Google class images

Google class images must be public HTTPS URLs because Google Wallet fetches them from the internet:

```python
EventTicketPassClass.make("concert").set_logo_url("https://cdn.example.com/logo.png")
```
