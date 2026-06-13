from website import create_webapp

webapp = create_webapp()

if __name__ == '__main__':
    webapp.run(debug=True)