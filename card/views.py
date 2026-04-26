from django.shortcuts import render, redirect
from django.http import HttpResponse
from .services import CardService, CardException
from .models import KnownKey, OperationLog


def dashboard(request):
    service = CardService()
    context = {
        'readers': [],
        'uid': None,
        'error': None
    }
    try:
        readers = service.get_readers()
        context['readers'] = [str(r) for r in readers]
        if readers:
            try:
                service.connect()
                context['uid'] = service.get_uid()
                service.disconnect()
            except Exception:
                pass  # no card on reader, that's fine
    except CardException as e:
        context['error'] = str(e)
    return render(request, 'card/dashboard.html', context)

def reader_status(request):
    service = CardService()
    readers = []
    try:
        readers = [str(r) for r in service.get_readers()]
    except Exception:
        pass
    return render(request, 'card/partials/reader_status.html', {'readers': readers})

def card_status(request):
    service = CardService()
    uid = None
    try:
        service.connect()
        uid = service.get_uid()
        service.disconnect()
    except Exception:
        pass
    return render(request, 'card/partials/card_status.html', {'uid': uid})

def dump_card(request):
    context = {'dump': None, 'error': None}
    if request.method == 'POST':
        service = CardService()
        try:
            sector_keys = {}
            known_keys = KnownKey.objects.all()
            for kk in known_keys:
                if kk.sector is not None:
                    sector_keys[kk.sector] = kk.as_list()
            service.connect()
            dump = service.dump_card(sector_keys)
            service.disconnect()
            context['dump'] = dump
            OperationLog.objects.create(
                operation=OperationLog.Operation.DUMP,
                status=OperationLog.Status.SUCCESS,
            )
        except CardException as e:
            context['error'] = str(e)
            OperationLog.objects.create(
                operation=OperationLog.Operation.DUMP,
                status=OperationLog.Status.FAILURE,
                error=str(e)
            )
    return render(request, 'card/dump.html', context)

def read_block(request):
    context = {
        'known_keys': KnownKey.objects.all(),
    }
    return render(request, 'card/read_block.html', context)


def read_block_action(request):
    if request.method != 'POST':
        return HttpResponse(status=405)

    sector = int(request.POST.get('sector', 0))
    block = int(request.POST.get('block', 0))
    key_hex = request.POST.get('key', 'FFFFFFFFFFFF')
    key = [int(key_hex[i:i+2], 16) for i in range(0, 12, 2)]
    block_number = (sector * 4) + block
    service = CardService()
    try:
        service.connect()
        service.load_key(key)
        service.authenticate(block_number)
        data = service.read_block(block_number)
        service.disconnect()
        hex_data = ' '.join(f'{b:02X}' for b in data)
        OperationLog.objects.create(
            operation=OperationLog.Operation.READ_BLOCK,
            status=OperationLog.Status.SUCCESS,
            sector=sector,
            block=block,
            data=hex_data
        )
        return render(request, 'card/partials/read_result.html', {
            'data': hex_data,
            'sector': sector,
            'block': block,
        })
    except CardException as e:
        OperationLog.objects.create(
            operation=OperationLog.Operation.READ_BLOCK,
            status=OperationLog.Status.FAILURE,
            sector=sector,
            block=block,
            error=str(e)
        )
        return render(request, 'card/partials/error.html', {'error': str(e)})

def write_block(request):
    context = {'error': None, 'success': False}
    if request.method == 'POST':
        sector = int(request.POST.get('sector', 0))
        block = int(request.POST.get('block', 0))
        key_hex = request.POST.get('key', 'FFFFFFFFFFFF')
        data_hex = request.POST.get('data', '')
        key = [int(key_hex[i:i+2], 16) for i in range(0, 12, 2)]
        data = [int(data_hex[i:i+2], 16) for i in range(0, 32, 2)]
        block_number = (sector * 4) + block
        service = CardService()
        try:
            service.connect()
            service.load_key(key)
            service.authenticate(block_number)
            service.write_block(block_number, data)
            service.disconnect()
            context['success'] = True
            OperationLog.objects.create(
                operation=OperationLog.Operation.WRITE_BLOCK,
                status=OperationLog.Status.SUCCESS,
                sector=sector,
                block=block,
                data=data_hex
            )
        except CardException as e:
            context['error'] = str(e)
            OperationLog.objects.create(
                operation=OperationLog.Operation.WRITE_BLOCK,
                status=OperationLog.Status.FAILURE,
                sector=sector,
                block=block,
                error=str(e)
            )
    return render(request, 'card/write_block.html', context)

def change_key(request):
    context = {'error': None, 'success': False}
    if request.method == 'POST':
        sector = int(request.POST.get('sector', 0))
        current_key_hex = request.POST.get('current_key', 'FFFFFFFFFFFF')
        new_key_hex = request.POST.get('new_key', '')
        current_key = [int(current_key_hex[i:i+2], 16) for i in range(0, 12, 2)]
        new_key = [int(new_key_hex[i:i+2], 16) for i in range(0, 12, 2)]
        trailer_block = (sector * 4) + 3
        service = CardService()
        try:
            service.connect()
            service.load_key(current_key)
            service.authenticate(trailer_block)
            from .apdu import SW_SUCCESS
            access_bits = [0xFF, 0x07, 0x80, 0x69]
            key_b = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
            trailer = new_key + access_bits + key_b
            service.write_block(trailer_block, trailer)
            service.disconnect()
            context['success'] = True
            OperationLog.objects.create(
                operation=OperationLog.Operation.CHANGE_KEY,
                status=OperationLog.Status.SUCCESS,
                sector=sector,
            )
        except CardException as e:
            context['error'] = str(e)
            OperationLog.objects.create(
                operation=OperationLog.Operation.CHANGE_KEY,
                status=OperationLog.Status.FAILURE,
                sector=sector,
                error=str(e)
            )
    return render(request, 'card/change_key.html', context)

def logs(request):
    logs = OperationLog.objects.all()[:100]
    return render(request, 'card/logs.html', {'logs': logs})

def logs_clear(request):
    if request.method != 'DELETE':
        return HttpResponse(status=405)
    OperationLog.objects.all().delete()
    return render(request, 'card/partials/logs_list.html', {'logs': []})

def keys(request):
    known_keys = KnownKey.objects.all()
    return render(request, 'card/keys.html', {'known_keys': known_keys})

def keys_add(request):
    if request.method != 'POST':
        return HttpResponse(status=405)
    name = request.POST.get('name')
    key = request.POST.get('key', '').upper().replace(' ', '')
    description = request.POST.get('description', '')
    sector = request.POST.get('sector', None)
    if len(key) != 12:
        return render(request, 'card/partials/error.html', {'error': 'Key must be exactly 12 hex characters'})
    KnownKey.objects.create(
        name=name,
        key=key,
        description=description,
        sector=sector if sector != '' else None
    )
    known_keys = KnownKey.objects.all()
    return render(request, 'card/partials/keys_list.html', {'known_keys': known_keys})

def keys_delete(request, pk):
    if request.method != 'DELETE':
        return HttpResponse(status=405)
    KnownKey.objects.filter(pk=pk).delete()
    known_keys = KnownKey.objects.all()
    return render(request, 'card/partials/keys_list.html', {'known_keys': known_keys})

def change_key(request):
    known_keys = KnownKey.objects.all()
    return render(request, 'card/change_key.html', {'known_keys': known_keys})

def change_key_action(request):
    if request.method != 'POST':
        return HttpResponse(status=405)

    sector = int(request.POST.get('sector', 0))
    current_key_hex = request.POST.get('current_key', 'FFFFFFFFFFFF').upper().replace(' ', '')
    new_key_hex = request.POST.get('new_key', '').upper().replace(' ', '')

    if len(current_key_hex) != 12 or len(new_key_hex) != 12:
        return render(request, 'card/partials/error.html', {'error': 'Keys must be exactly 12 hex characters'})

    current_key = [int(current_key_hex[i:i+2], 16) for i in range(0, 12, 2)]
    new_key = [int(new_key_hex[i:i+2], 16) for i in range(0, 12, 2)]
    trailer_block = (sector * 4) + 3

    service = CardService()
    try:
        service.connect()
        service.load_key(current_key)
        service.authenticate(trailer_block)
        access_bits = [0xFF, 0x07, 0x80, 0x69]
        key_b = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
        trailer = new_key + access_bits + key_b
        service.write_block(trailer_block, trailer)
        service.disconnect()
        OperationLog.objects.create(
            operation=OperationLog.Operation.CHANGE_KEY,
            status=OperationLog.Status.SUCCESS,
            sector=sector,
        )
        return render(request, 'card/partials/change_key_result.html', {
            'sector': sector,
            'new_key': new_key_hex,
        })
    except CardException as e:
        OperationLog.objects.create(
            operation=OperationLog.Operation.CHANGE_KEY,
            status=OperationLog.Status.FAILURE,
            sector=sector,
            error=str(e)
        )
        return render(request, 'card/partials/error.html', {'error': str(e)})