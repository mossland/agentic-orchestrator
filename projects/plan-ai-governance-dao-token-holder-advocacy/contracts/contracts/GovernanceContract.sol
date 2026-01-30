// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/structs/EnumerableSet.sol";

contract GovernanceContract is Ownable {
    using EnumerableSet for EnumerableSet.Bytes32Set;

    struct AuditLog {
        string auditType;
        uint256 timestamp;
    }

    mapping(address => AuditLog[]) private auditLogs;

    event AuditLogSubmitted(address indexed userId, string auditType);

    modifier onlyValidAddress(address _userId) {
        require(_userId != address(0), "Invalid user address");
        _;
    }

    function submitAuditLog(string memory auditType, address userId)
        public
        onlyOwner
        onlyValidAddress(userId)
    {
        AuditLog memory newLog = AuditLog({
            auditType: auditType,
            timestamp: block.timestamp
        });
        auditLogs[userId].push(newLog);
        emit AuditLogSubmitted(userId, auditType);
    }

    function getAuditLogsByUser(address userId) public view returns (AuditLog[] memory) {
        return auditLogs[userId];
    }
}