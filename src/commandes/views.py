from django.shortcuts import render
from django.views.generic import ListView, CreateView
from django.shortcuts import get_object_or_404
from articles.models import Article
from .models import Panier, ValidatedOrder, LigneCommande
from django.views.generic.edit import DeleteView
from django.views.generic.detail import DetailView
from django.db.models import Sum
from django.shortcuts import redirect
from django.urls import reverse_lazy
from accounts.models import UserProfile
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Q, Max
from django.utils import timezone

from django.contrib import messages

# Create your views here.

class PanierCreate(CreateView):
    model = Panier
    template_name = "commande/create_panier.html"
    fields = ["quantity" ]
    success_message = "Article ajouté avec succes"

    def form_valid(self, form):
        article = get_object_or_404(Article, slug=self.kwargs['slug'])
        panier = Panier.objects.filter(user=self.request.user)
        if article.name not in [i.articles.name for i in panier]:
            form.instance.articles = article
            form.instance.user = self.request.user
            return super(PanierCreate, self).form_valid(form)
        else :
            instance = panier.get(articles=article)
            instance.quantity += form.instance.quantity
            instance.save()
            return redirect('commande:home')

class PanierHome(ListView):
    model = Panier
    context_object_name = "panier"
    template_name = "commande/panier_list.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        panier = Panier.objects.filter(user=self.request.user)
        prof = UserProfile.objects.get(user=self.request.user)
        context["price_tot"] = panier.aggregate(Sum('price'))['price__sum']
        context["nb_art_tot"] = panier.aggregate(Sum('quantity'))['quantity__sum']

        context["tot_achat"] = prof.number_of_purchase
        if context["nb_art_tot"] and context["price_tot"]:
            if (context["nb_art_tot"] + context["tot_achat"]) > prof.reduction_threshold :
                context["sum_reduc"] = context["price_tot"] * 0.9
                context["reduc"] = "10 %"
            else:
                context["reduc"] = "Non eligible à une reduction"
                context["sum_reduc"] = context["price_tot"]
        return context

    def get_queryset(self):

        queryset = super().get_queryset()
        return queryset.filter(user = self.request.user)

class DeletePanier(UserPassesTestMixin, DeleteView):
    model = Panier
    context_object_name = "panier"
    template_name = "commande/pannier_confirm_delete.html"
    success_url = reverse_lazy('commande:home')

    def test_func(self, *args, **kwargs):
        return self.request.user.is_superuser or self.get_object() in Panier.objects.filter(user=self.request.user)

class CreateCommande(CreateView):
    model = Panier
    template_name = "commande/create_commande.html"
    fields = []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        panier = Panier.objects.filter(user=self.request.user)
        context["nb_art_tot"] = panier.aggregate(Sum('quantity'))['quantity__sum']
        return context

    def form_valid(self, form, **kwargs):
        panier = Panier.objects.filter(user=self.request.user)
        
        if len(panier) > 0:
            userprofile = UserProfile.objects.get(user=self.request.user)

            vd = ValidatedOrder.objects.create(user=self.request.user)
            vd.tot_price_and_quantity_calculation()
            msg = ""
            for article in panier:
                lg = LigneCommande.objects.create(order=vd, article=article.articles, quantity=article.quantity)
                lg.save()
                vd.articles.add(article.articles)
                verif_stock = article.articles.set_stock(article.quantity)

                if verif_stock:
                    msg += f"{verif_stock} unité de '{article.articles.name}' dans le stock, "
            
            vd.reduction = userprofile.set_number_of_purchase(vd.tot_quantity)
            vd.save()

            Panier.objects.filter(user=self.request.user).delete()
            messages.success(self.request, "Commande Effectuée")

            if msg:
                msg = "Il manque " + msg + "l'expédition sera effectuée dès le prochain réaprovisionnement de stock"
                messages.error(self.request, msg)
        else :
            messages.error(self.request, "Vous n'avez aucun articles dans votre panier")

        return redirect('commande:home')



class UniqueCommande(CreateView):
    model = ValidatedOrder
    template_name = "commande/create_unique_commande.html"
    fields = [ "tot_quantity" ]
    success_url = reverse_lazy('articles:home')

    def form_valid(self, form):
        article = get_object_or_404(Article, slug=self.kwargs['slug'])
        if article :
            tot_price = article.price * form.instance.tot_quantity
            user = self.request.user
            userprofile = UserProfile.objects.get(user=user)

            vd = ValidatedOrder.objects.create(user=self.request.user, tot_price=tot_price, tot_quantity=form.instance.tot_quantity)
            lg = LigneCommande.objects.create(order=vd, article=article, quantity=form.instance.tot_quantity)
            lg.save()
            vd.articles.add(article)
            vd.reduction = userprofile.set_number_of_purchase(form.instance.tot_quantity)
            vd.save()
            verif_stock = article.set_stock(form.instance.tot_quantity)
            
            messages.success(self.request, "Commande Effectuée")
            if verif_stock:
                messages.error(self.request, f"Il manque {verif_stock} unité de '{article.name}' dans le stock, l'expédition sera effectuée dès le prochain réaprovisionnement de stock")

        else :
            messages.error(self.request, "Vous n'avez aucun articles dans votre panier")
            
        return redirect('commande:home')


class CommandeHome(UserPassesTestMixin, ListView):
    model = ValidatedOrder
    context_object_name = "commande"
    template_name = "commande/validatedorder_list.html"

    def test_func(self, *args, **kwargs):
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['max_quatity'] = ValidatedOrder.objects.all().aggregate(Max('tot_quantity'))['tot_quantity__max']
        context['max_price'] = ValidatedOrder.objects.all().aggregate(Max('tot_price'))['tot_price__max']
        context['max_date'] = ValidatedOrder.objects.all().aggregate(Max('created_on'))['created_on__max']
        
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')

        if query is not None :
            if 'q' in self.request.GET:
                return queryset.filter( Q(user__username__icontains=query)).order_by('-created_on')
        elif 'q1' in self.request.GET:
            req = self.request.GET['q1']
            if req == 'Année':
                return queryset.filter(created_on__year=timezone.now().year)
            elif req == 'Jour':
                return queryset.filter(created_on__year=timezone.now().year).filter(created_on__day=timezone.now().day).filter(created_on__month=timezone.now().month)
            elif req == 'Mois':
                return queryset.filter(created_on__year=timezone.now().year).filter(created_on__month=timezone.now().month)

        elif 'q2' in self.request.GET:
            query = self.request.GET.get('q2')
            if query == "Quantité" or query == "+Quantité":
                return self.sort_queryset(query, queryset, 'Quantité', 'tot_quantity')

            elif query == "Prix total" or query == "+Prix total":
                return self.sort_queryset(query, queryset, 'Prix total', 'tot_price')

            elif query == "Date" or query == "+Date":
                return self.sort_queryset(query, queryset, 'Date', 'created_on')

            elif query == "Reduction" or query == "+Reduction":
                return self.sort_queryset(query, queryset, 'Reduction', 'reduction')

        return queryset

    def sort_queryset(self, query, queryset, strsort, col):
        if query == '+' + strsort :
            return queryset.order_by(col)
        elif query == strsort :
            return queryset.order_by('-' + col)

class DeleteCommande(UserPassesTestMixin, DeleteView):
    model = ValidatedOrder
    context_object_name = "commande"
    template_name = "commande/validatedorder_confirm_delete.html"
    success_url = reverse_lazy('commande:stat')

    def test_func(self, *args, **kwargs):
        return self.request.user.is_superuser


class DetailCommande(UserPassesTestMixin, DetailView):
    model = ValidatedOrder
    context_object_name = "commande"
    template_name = "commande/validatedorder_detail.html"
    success_url = reverse_lazy('commande:stat')

    def test_func(self, *args, **kwargs):
        print(self.request.resolver_match.kwargs.get('pk'))
        order = ValidatedOrder.objects.get(pk=self.request.resolver_match.kwargs.get('pk'))
        return self.request.user.is_superuser or order.user == self.request.user

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["articles"] = LigneCommande.objects.filter(order=kwargs['object'])
        return context

class MyOrders(ListView):
    model = ValidatedOrder
    context_object_name = "commande"
    template_name = "commande/my_validatedorder_list.html"


    def get_queryset(self):
        queryset = super().get_queryset().filter(user=self.request.user)

        return queryset
