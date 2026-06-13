$('.plus-cart').click(function(){
    console.log('Button clicked')

    var id = $(this).attr('pid').toString()
    var quantity = this.parentNode.children[1]

    $.ajax({
        type: 'GET',
        url: '/plus_cart',
        data: {
            cart_id: id
        },
        
        success: function(details){
            console.log(details)
            quantity.innerText = details.quantity
            document.getElementById(`quantity${id}`).innerText = details.quantity
            document.getElementById('amount_tt').innerText = details.amount
            document.getElementById('totalamount').innerText = details.total

        }
    })
})


$('.minus-cart').click(function(){
    console.log('Button clicked')

    var id = $(this).attr('pid').toString()
    var quantity = this.parentNode.children[1]

    $.ajax({
        type: 'GET',
        url: '/minus_cart',
        data: {
            cart_id: id
        },
        
        success: function(details){
            console.log(details)
            quantity.innerText = details.quantity
            document.getElementById(`quantity${id}`).innerText = details.quantity
            document.getElementById('amount_tt').innerText = details.amount
            document.getElementById('totalamount').innerText = details.total

        }
    })
})


$('.remove-cart').click(function(){
    
    var id = $(this).attr('pid').toString()

    var to_remove = this.parentNode.parentNode.parentNode.parentNode

    $.ajax({
        type: 'GET',
        url: '/remove_cart_product',
        data: {
            cart_id: id
        },

        success: function(details){
            document.getElementById('amount_tt').innerText = details.amount
            document.getElementById('totalamount').innerText = details.total
            to_remove.remove()
        }
    })


})
