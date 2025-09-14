def create_blend_label_zpl(name, id, allergens):
    try:
        zpl = f"""
new
"""
        print(name, id, allergens)

        # get pallet structure name then apply the applicable variables

        # then make the label string with the XA and XZ commands
        return zpl
    except Exception as ex:
        print("Data could not be processed: \n", ex)
