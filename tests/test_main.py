from unittest.mock import patch
import sys
import os
import pytest


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import main
import miner



@patch("main.choose_placement")
@patch("main.choose_functionality")
@patch("main.modification.initiate_files")
def test_user_input(mock_inititate_files, mock_choose_functionality, mock_choose_placement):
    main.user_input()
    mock_inititate_files.assert_called_once()
    mock_choose_functionality.assert_called_once()
    mock_choose_placement.assert_called_once()



@patch("builtins.input",side_effect=["bad input","1"])
@patch("main.output.choose_functionality")
def test_choose_functionality(mock_choose_functionality, mock_input, capsys):
    main.choose_functionality()
    mock_choose_functionality.assert_called()
    assert "Input is incorrect, try again..!" in capsys.readouterr().out
    assert main.blockchainFunction==1


@patch("builtins.input", side_effect=["bad input", "2"])
@patch("main.output.choose_placement")
def test_choose_placement(mock_choose_placement, mock_input, capsys):
    main.choose_placement()
    mock_choose_placement.assert_called()
    assert "Input is incorrect, try again..!" in capsys.readouterr().out
    assert main.blockchainPlacement == 2


@patch("builtins.input", side_effect=["example input","example_input2", "done"])
@patch.object(main.end_user.User,"send_tasks")
@patch.object(main.end_user.User,"create_tasks")
@patch("main.output.user_identity_addition_reminder")
@patch("main.output.GDPR_warning")
@patch("main.output.users_and_fogs_are_up")
@patch("main.Fog.Fog")
@pytest.mark.parametrize("func",[1,2,3,4])
def test_initiate_network(mock_fog,mock_users_fogs,mock_GDPR,mock_user_reminder,mock_user_ct,mock_user_st, mock_input, capsys,func):
    main.list_of_end_users.clear()
    main.fogNodes.clear()
    main.blockchainFunction=func
    main.initiate_network()
    assert mock_fog.call_count == main.NumOfFogNodes
    assert len(main.list_of_end_users)==main.NumOfFogNodes*main.num_of_users_per_fog_node
    mock_users_fogs.assert_called_once()
    readerout = capsys.readouterr()
    if main.blockchainFunction==4:
        mock_GDPR.assert_called_once()
        assert "If you don't want other attributes to be added to end_users, input: done\n" in readerout.out
        for user in main.list_of_end_users:
            assert "example input" in user.identity_added_attributes.keys()
            assert "example_input2" in user.identity_added_attributes.keys()
        mock_user_reminder.assert_called()
    assert mock_user_ct.call_count == len(main.list_of_end_users)
    assert mock_user_st.call_count == len(main.list_of_end_users)
    assert "had sent its tasks to the fog layer" in readerout.out


@patch("main.output.miners_are_up")
@patch("main.connect_miners")
@patch("main.modification.rewrite_file")
@patch("main.modification.read_file")
@patch("main.modification.write_file")
@patch("main.miner.Miner")
@pytest.mark.parametrize("placement",[1,2])
def test_inititate_miners(mock_miner,mock_write_file,mock_read_file,mock_rewrite_file,mock_connect_miners,mock_miners_up,capsys,placement):
    main.blockchainPlacement=placement
    miners_list=main.initiate_miners()
    if main.blockchainPlacement==1:
        assert len(miners_list)==main.NumOfFogNodes
        assert mock_miner.call_count == main.NumOfFogNodes
    if main.blockchainPlacement==2:
        assert len(miners_list)==main.NumOfMiners
        assert mock_miner.call_count == main.NumOfMiners
    assert mock_write_file.call_count == len(miners_list)
    assert mock_read_file.call_count == len(miners_list)
    assert mock_rewrite_file.call_count == len(miners_list)
    readerout = capsys.readouterr()
    assert "Miners have been initiated.." in readerout.out
    mock_connect_miners.assert_called_once()
    mock_miners_up.assert_called_once()
    assert isinstance(miners_list,list)




@pytest.mark.parametrize("layer",[1,2])
def test_define_trans_delay(layer):
    transmission_delay=main.define_trans_delay(layer)
    if layer==1:
        assert transmission_delay == main.delay_between_fog_nodes
    if layer==2:
        assert transmission_delay == main.delay_between_end_users
    assert isinstance(transmission_delay,int)


@patch("main.bridging")
@patch("main.create_components")
def test_connect_miners(mock_create_components,mock_bridging,capsys):
    main.connect_miners([])
    readerout = capsys.readouterr()
    assert "Miners will be connected in a P2P fashion now. Hold on..." in readerout.out
    mock_create_components.assert_called_once()
    mock_bridging.assert_called_once()



def create_faux_miners(ran):
    miners_list = []
    for i in range(ran):
        miners_list.append(miner.Miner(i + 1, 0, True))
    return miners_list




@pytest.mark.parametrize("ran",[5,20,50])
def test_create_components(ran):
    miners_list = create_faux_miners(ran)
    components=main.create_components(miners_list)
    assert len(components)<ran
    assert isinstance(components,set)


