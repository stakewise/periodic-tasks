from src.common.settings import NETWORK, SENTRY_DSN


def setup_sentry() -> None:
    if not SENTRY_DSN:
        return
    # pylint: disable-next=import-outside-toplevel
    import sentry_sdk

    sentry_sdk.init(
        SENTRY_DSN,
        traces_sample_rate=0.1,
        environment=NETWORK.value,
    )
    sentry_sdk.set_tag('network', NETWORK)
