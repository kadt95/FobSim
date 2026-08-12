import sys
import os
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..","..")))
import encryption_module


@patch("encryption_module.rsa")
@patch("builtins.open")
def test_generate_PKI_keys(mock_open,mock_rsa):
    mock_pub_key = MagicMock()
    mock_pri_key = MagicMock()
    mock_rsa.newkeys.return_value = [mock_pub_key, mock_pri_key]
    mock_pri_key.save_pkcs1.return_value = "test"
    mock_pub_key.save_pkcs1.return_value = "test"
    encryption_module.generate_PKI_keys(2048, "test")
    assert mock_open.call_count == 2
    assert 'temporary/test_private.key' in str(mock_open.call_args_list)
    assert 'temporary/test_public.key' in str(mock_open.call_args_list)

@patch("encryption_module.pathlib.Path")
@patch("encryption_module.rsa")
@patch("builtins.open")
@pytest.mark.parametrize("pri_or_pub",["private","public"])
def test_retrieve_key_from_saved_file(mock_open,mock_rsa,mock_pathlib,pri_or_pub):
    fake_private_key = SimpleNamespace()
    fake_public_key = SimpleNamespace()
    mock_rsa.PrivateKey.load_pkcs1.return_value = fake_private_key
    mock_rsa.PublicKey.load_pkcs1.return_value = fake_public_key
    key = encryption_module.retrieve_key_from_saved_file("test",pri_or_pub)
    if pri_or_pub == "private":
        assert key == fake_private_key
    if pri_or_pub == "public":
        assert key == fake_public_key


@patch("encryption_module.rsa")
@pytest.mark.parametrize("pri_or_pub",["private","public"])
def test_prepare_key_for_use_actual_key(mock_rsa,pri_or_pub):
    fake_private_key = SimpleNamespace()
    fake_public_key = SimpleNamespace()
    mock_rsa.PrivateKey.load_pkcs1.return_value = fake_private_key
    mock_rsa.key.PublicKey.load_pkcs1.return_value = fake_public_key
    key = encryption_module.prepare_key_for_use(pri_or_pub,None,"test")
    if pri_or_pub == "private":
        assert key == fake_private_key
    if pri_or_pub == "public":
        assert key == fake_public_key

@patch("encryption_module.rsa")
@patch("encryption_module.retrieve_key_from_saved_file")
def test_prepare_key_for_use_saved_key(mock_retrieve,mock_rsa):
    encryption_module.prepare_key_for_use("private","test",None)
    mock_retrieve.assert_called_once_with("test","private")


@patch("encryption_module.rsa")
@pytest.mark.parametrize("pri_or_pub",["private","public"])
def test_serialize_key(mock_rsa,pri_or_pub):
    fake_private_key = SimpleNamespace()
    fake_public_key = SimpleNamespace()
    mock_rsa.key.PrivateKey.load_pkcs1.return_value = fake_private_key
    mock_rsa.key.PublicKey.load_pkcs1.return_value = fake_public_key
    key = encryption_module.serialize_key("test",pri_or_pub)
    if pri_or_pub == "private":
        assert key == fake_private_key
    if pri_or_pub == "public":
        assert key == fake_public_key
