from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from .forms import *
from django.contrib import messages
from .models import *



from .models import Category, Product

def index(request):
    user = request.user
    posts = Product.objects.all().order_by('name')[:21]
    cats = Category.objects.all()

    wish_item = []
    if user.is_authenticated:
        wish_item = WishListItem.objects.filter(user=user).values_list('product__id', flat=True)
    else:
        wish_item = []

    context = {
            'posts': posts,
            'cats': cats,
            'cat_selected': 0,
            'user': user,
            'wish_item': wish_item,
    }

    return render(request, 'main/index.html', context=context)

def about(request):
    return render(request, 'main/about_us.html')

def user_data(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.phone = request.POST.get('phone')
        user.save()

        messages.success(request, 'Профіль успішно оновлено.')
        return redirect('profile')
    return render(request, 'main/user_data.html')

def update_address(request):
    if request.method == 'POST':
        form = UpdateAddresForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Адресу успішно оновлено.')
            return redirect('profile')
        else:
            messages.error(request, 'Будь ласка, виправте помилки в формі.')
    else:
        form = UpdateAddresForm(instance=request.user)
    return render(request, 'main/adress.html', {'form': form})


def change_pass(request):
    if request.method == 'POST':
        old_password = request.POST['old_password']
        new_password1 = request.POST['new_password1']
        new_password2 = request.POST['new_password2']

        user = request.user

        if user.check_password(old_password) and new_password1 == new_password2:
            user.set_password(new_password1)
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Пароль успішно змінено.')
            return redirect('profile')
        else:
            messages.error(request, 'Невірний старий пароль або нові паролі не співпадають.')
    return render(request, 'main/chanage_pas.html')



def user_profile(request):
    return render(request, 'main/user_profile.html')

def categories(request):
    cats = Category.objects.all()
    context = {
        'cats': cats,
    }

    return render(request, 'main/categories.html', context=context)

def category_product(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    products = Product.objects.filter(cat=category)

    context = {
        'category': category,
        'products': products,
        'px': category_id,
    }

    return render(request, 'main/category_product.html', context=context)

def delivery(request):
    return render(request, 'main/delivery.html')


def product_page(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    recommended_products = Product.objects.filter(cat=product.cat).exclude(id=product_id)[:4]
    user = request.user

    if user.is_authenticated:
        wish_item = WishListItem.objects.filter(user=user).values_list('product__id', flat=True)
    else:
        wish_item = []

    context = {
        'product': product,
        'recommended_products': recommended_products,
        'wish_item': wish_item,
    }
    return render(request, 'main/product_page.html', context=context)

def login_request(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(email=email, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f'Ви ввійшли як {user}.')
                return redirect('home')
            else:
                messages.error(request, 'Невірний email або пароль.')
        else:
            messages.error(request, 'Невірний email або пароль.')
    form = AuthenticationForm()
    return render(request=request, template_name='main/login.html', context={'login_form': form})

def logout_request(request):
    logout(request)
    messages.info(request, "Ви успішно вийшли з акаунта!")
    return redirect('home')

def registration(request):
    if request.method == 'POST':
        form = NewUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Ви успішно зареєструвались.')
            return redirect('home')
        else:
            messages.error(request, "Неуспішна реєстрація. Невірна інформація.")
    else:
        form = NewUserForm()
    return render(request=request, template_name='main/register.html', context={'register_form': form})

def error_404(request, exception):
    return render(request, 'main/404.html')

# Function for searching the site
def search(request):
    query = request.GET.get('q')
    if query:
        # This option to search all databases

        # products = Product.objects.filter(name__icontains=query)

        # This option for searching the SQLite database
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(name__icontains=query.capitalize())
        )
    else:
        products = Product.objects.none()

    context = {
        'Products': products,
        'q': query
    }
    return render(request, 'main/search.html', context=context)

@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    user = request.user

    # if request.method == 'POST':
    #     WishListItem.objects.create(user=user, product=product)

    if WishListItem.objects.filter(user=user, product=product).exists():
        return redirect('home')
    else:
        # Add the item to the wishlist
        WishListItem.objects.create(user=user, product=product)

    return redirect('wishlist')


@login_required
def wishlist(request):
     wishlist_items = WishListItem.objects.filter(user=request.user)
     return render(request, 'main/wishlist.html', {'wishlist_items': wishlist_items})

@login_required
def remove_wishlist(request, item_id):
    item = get_object_or_404(WishListItem, pk=item_id)
    if item.user == request.user:
        item.delete()
    return redirect('wishlist')

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    user = request.user

    if request.method == 'POST':
        size = request.POST.get('size')

        if not size:
            messages.error(request, 'Please select a size before adding to the cart.', extra_tags='size_not_selected')
            return redirect('product_page', product_id=product_id)
        else:
            cart_items = CartItem.objects.filter(user=user, product=product, size=size)

        if cart_items.exists():
            cart_item = cart_items.first()
            cart_item.quantity += 1
            cart_item.save()
        else:
            CartItem.objects.create(user=user, product=product, quantity=1, size=size)

        return redirect('cart')

    return redirect('product_page', product_id=product_id)

@login_required
def cart(request):
    user = request.user
    cart_items = CartItem.objects.filter(user=user)
    total_price = 0

    for item in cart_items:
        item_price = item.product.main_price
        item_price_discount = item.product.discount_price
        item_quantity = item.quantity
        if item_price and item_price_discount:
            total_price += int(item_price_discount) * item_quantity
        elif item_price:
            total_price += int(item_price) * item_quantity

    context = {
        'cart_items': cart_items,
        'total_price': total_price
    }

    return render(request, 'main/cart.html', context=context)

@login_required
def update_cart_quantity(request, product_id):
    if request.method == 'POST':
        new_quantity = int(request.POST.get('quantity', 1))
        if new_quantity < 1:
            new_quantity = 1

        user = request.user
        cart_items = CartItem.objects.filter(user=user, product_id=product_id)

        if cart_items.exists():
            for cart_item in cart_items:
                cart_item.quantity = new_quantity
                cart_item.save()

    return redirect('cart')

def remove_product(request, product_id, size):
    user = request.user
    try:
        # Filter CartItem by product_id and size for the current user
        cart_item = CartItem.objects.get(user=user, product_id=product_id, size=size)
        cart_item.delete()
        return redirect('cart')
    except CartItem.DoesNotExist:
        # Handle the case where the CartItem does not exist
        return messages.error(request, "CartItem not found")


@login_required
def order_view(request):
    user = request.user
    cart_items = CartItem.objects.filter(user=user)
    total_price = 0

    for item in cart_items:
        item_price = item.product.main_price
        item_price_discount = item.product.discount_price
        item_quantity = item.quantity
        if item_price and item_price_discount:
            total_price += int(item_price_discount) * item_quantity
        elif item_price:
            total_price += int(item_price) * item_quantity

    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = user
            order.save()

            for item in cart_items:
                OrderItem.objects.create(
                    user=user, product=item.product,
                    quantity=item.quantity,
                    size=item.size,
                    addres=form.cleaned_data['addres'],
                    delivery_method=form.cleaned_data['delivery_method'],
                    payment_method=form.cleaned_data['payment_method']
                )
                item.product.sold += item.quantity
                item.product.save()
                OrderItem.objects.filter(user=user).delete()
                messages.success(request, 'Your order has been successfully placed. Thank you!')
            return redirect('home')
    else:
        form = OrderForm()

    context = {
        'form': form,
        'cart_items': cart_items,
        'total_price': total_price
    }

    return render(request, 'main/order.html', context=context)
