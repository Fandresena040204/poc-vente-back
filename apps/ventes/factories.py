import factory

from apps.accounts.models import Customer
from apps.ventes.models import Product, Vente, VenteLigne


class CustomerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Customer

    name = factory.Faker('company')
    email = factory.Faker('email')


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Faker('word')
    sku = factory.Sequence(lambda n: f'SKU-{n:05d}')
    default_price = 10


class VenteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Vente

    customer = factory.SubFactory(CustomerFactory)


class VenteLigneFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = VenteLigne

    vente = factory.SubFactory(VenteFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = 1
    unit_price = 10
