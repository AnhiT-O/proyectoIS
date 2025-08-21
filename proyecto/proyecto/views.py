from django.http import HttpResponse


def hola_mundo(request):
    """
    Vista simple que muestra un mensaje de Hola Mundo
    """
    html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Casa de Cambios - Hola Mundo</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }
            .container {
                background: white;
                padding: 2rem;
                border-radius: 10px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                text-align: center;
                max-width: 500px;
            }
            h1 {
                color: #333;
                margin-bottom: 1rem;
            }
            p {
                color: #666;
                font-size: 1.1rem;
                line-height: 1.6;
            }
            .emoji {
                font-size: 3rem;
                margin-bottom: 1rem;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="emoji">🏦💱</div>
            <h1>¡Hola Mundo!</h1>
            <p>Bienvenido al proyecto <strong>Casa de Cambios</strong></p>
            <p>Tu aplicación Django está funcionando correctamente.</p>
            <p><em>¡Felicidades por configurar tu primer proyecto!</em></p>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html)
