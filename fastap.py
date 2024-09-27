async def analyzetext(request: Request):
    print("Entrei no metodo post fastapi!")
    content_type = request.headers.get('Content-Type')
    
    if content_type is None:
        raise HTTPException(status_code=400, detail='No Content-Type provided')
    elif content_type == 'application/json':
        try:
            data = await request.json()
            print("Data: ", data['string'])
            return {'message': ianlp.connect(data['string'], nlp)}
        except JSONDecodeError:
            raise HTTPException(status_code=400, detail='Invalid JSON data')
    else:
        raise HTTPException(status_code=400, detail='Content-Type not supported')