from aws_lambda_powertools.tracing import Tracer
from aws_lambda_powertools.logging.logger import set_package_logger

def test_package_logger(capsys):
    import aws_lambda_powertools
    set_package_logger()
    tracer = Tracer(disabled=True)
    output = capsys.readouterr()
    
    assert "Tracing has been disabled" in output.out
