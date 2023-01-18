import xmlrpc.client
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import click


@click.command(
    help="Injects a test mail into an Odoo instance. Will create a 'LOCAL TEST' incoming"
    " mailserver.\n\n"
    "Make sure that an alias is set up to catch whatever recipient you choose here!",
)
@click.option('-d', '--database', default='odoo', help='Odoo database name', show_default=True)
@click.option('-u', '--userid', default=2, type=int,
    help='Odoo user id to connect with', show_default=True)
@click.option('-p', '--password', default='admin', help='Odoo user password', show_default=True)
@click.option('-h', '--host', default='localhost', help='Odoo host', show_default=True)
@click.option('--port', default=8069, type=int, help='Odoo port', show_default=True)
@click.option('-b', '--body', default='This is a test mail.',
    help='Body of the mail', show_default=True)
@click.option('-s', '--subject', default='Test', help='Subject of the mail', show_default=True)
@click.option('--sender', default='test@example.com', help='Sender of the mail', show_default=True)
@click.option('-r', '--recipient', required=True, help='Recipient of the mail')
def main(
    database: str, userid: int, password: str, host: str , port: int, body: str, subject: str,
    sender: str, recipient: str,
):
    models = connect(host, port)
    assert_local_mailserver(models, database, userid, password)
    mail = create_mail(subject, body, sender, recipient)
    inject_mail(models, database, userid, password, mail)
    print("Mail sent")


def connect(host: str, port: int) -> 'ServerProxy':
    return xmlrpc.client.ServerProxy(f'http://{host}:{port}/xmlrpc/2/object', allow_none=True)


def assert_local_mailserver(
    models: 'ServerProxy', database: str, userid: int, password: str
) -> None:
    """Makes sure there is a local mail server set"""
    res = models.execute_kw(
        database, userid, password,
        'fetchmail.server', 'search',
        [[['server_type', '=', 'local']]],
        {'limit': 1}
    )
    if not res:
        models.execute_kw(
            database, userid, password,
            'fetchmail.server', 'create',
            [{
                'name': 'LOCAL TEST',
                'server_type': 'local',
            }],
        )


def create_mail(subject: str, body: str, sender: str, recipient: str) -> str:
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(body, "plain"))
    return str(msg)


def inject_mail(
    models: 'ServerProxy', database: str, userid: int, password: str, mail: str
) -> None:
    models.execute_kw(
        database, userid, password,
        'mail.thread', 'message_process',
        [None, mail], {},
    )


if __name__ == '__main__':
    main()
