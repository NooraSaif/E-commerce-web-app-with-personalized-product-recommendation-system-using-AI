from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, PasswordField, EmailField, SubmitField, SelectField
from wtforms.validators import DataRequired, length, NumberRange
from flask_wtf.file import FileField

class RegistrForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    user_name = StringField('Username', validators=[DataRequired(), length(min=2)])
    phone_number = IntegerField('Phone Number', validators=[DataRequired(), NumberRange(min=0)])
    password1 = PasswordField('Enter Your Password', validators=[DataRequired(), length(min=6)])
    password2 = PasswordField('Confirm Your Password', validators=[DataRequired(), length(min=6)])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(),])
    password = PasswordField('Enter Your Password', validators=[DataRequired()])
    submit = SubmitField('Log in')

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Current Password', validators=[DataRequired(), length(min=6)])
    new_password = PasswordField('New Password', validators=[DataRequired(), length(min=6)])
    confirm = PasswordField('Confirm New Password', validators=[DataRequired(), length(min=6)])
    change = SubmitField('Change Password')

class ProductsForm(FlaskForm):
    product_name = StringField('Name of Product', validators=[DataRequired()])
    price = FloatField('Current Price', validators=[DataRequired()])
    description = StringField('description of Product', validators=[DataRequired()])
    in_stock = IntegerField('In Stock', validators=[DataRequired(), NumberRange(min=0)])
    main_category = SelectField('Main Category', choices=[('Electronics', 'Electronics'),('Office Products', 'Office Products'),('Computers', 'Computers'), ('Home', 'Home')], validators=[DataRequired()])
    sub_category = SelectField('Sub Category', choices=[

        ('Cables', 'Cables'), ('NetworkAdapters', 'NetworkAdapters'), ('LaptopAccessories', 'LaptopAccessories'),
        ('PenDrives', 'PenDrives'), ('Keyboards,Mice', 'Keyboards,Mice'), ('ExternalHardDisks', 'ExternalHardDisks'),
        ('Repeaters', 'Repeaters'), ('Inks,Toners', 'Inks,Toners'), ('PCGamingPeripherals', 'PCGamingPeripherals'),
        ('HardDiskBags', 'HardDiskBags'), ('Routers', 'Routers'), ('Adapters', 'Adapters'), ('USBGadgets', 'USBGadgets'),
        ('TabletAccessories', 'TabletAccessories'), ('USBHubs', 'USBHubs'), ('Audio', 'Audio'),
        ('UninterruptedPowerSupplies', 'UninterruptedPowerSupplies'), ('InternalSolidStateDrives', 'InternalSolidStateDrives'),
        ('Printers', 'Printers'),('Paper', 'Paper'),

        ('Accessories', 'Accessories'), ('Televisions', 'Televisions'), ('Projectors', 'Projectors'),
        ('SatelliteEquipment', 'SatelliteEquipment'),('Speakers', 'Speakers'), ('SmartWatches', 'SmartWatches'),
        ('MobileAccessories', 'MobileAccessories'), ('Smartphones', 'Smartphones'), ('MemoryCards', 'MemoryCards'),
        ('Headphones', 'Headphones'), ('DisposableBatteries', 'DisposableBatteries'),
        ('RechargeableBatteries', 'RechargeableBatteries'), ('SecurityCameras', 'SecurityCameras'),('SurgeProtectors', 'SurgeProtectors')
    ], validators=[DataRequired()])
    product_picture = FileField('Product image')

    add_product = SubmitField('Add Product')
    update_product = SubmitField('Update')

class OrderForm(FlaskForm):
    status = SelectField('Order Status', choices=[('Confirmed', 'Confirmed'), ('Packaging', 'Packaging'),
                                                        ('Shipped', 'Shipped'),
                                                        ('Delivered', 'Delivered')])

    change = SubmitField('change status')
