import { expect } from "chai";
import { ethers } from "hardhat";

describe("DAO Governance Token Contract", function () {
  let daoGovernanceToken: any;
  let owner: any;
  let addr1: any;
  let addr2: any;

  beforeEach(async function () {
    const DAOContract = await ethers.getContractFactory("DAOGovernanceToken");
    [owner, addr1, addr2] = await ethers.getSigners();
    daoGovernanceToken = await DAOContract.deploy(owner.address);
    await daoGovernanceToken.deployed();
  });

  describe("Deployment", function () {
    it("Should set the right owner", async function () {
      expect(await daoGovernanceToken.owner()).to.equal(owner.address);
    });
  });

  describe("Public Functions", function () {
    beforeEach(async function () {
      await daoGovernanceToken.mint(addr1.address, ethers.utils.parseEther("10"));
      await daoGovernanceToken.transferOwnership(addr2.address);
    });

    it("Should mint tokens to an address", async function () {
      expect(await daoGovernanceToken.balanceOf(addr1.address)).to.equal(ethers.utils.parseEther("10"));
    });

    it("Should transfer ownership of the contract", async function () {
      expect(await daoGovernanceToken.owner()).to.equal(addr2.address);
    });
  });

  describe("Access Control", function () {
    beforeEach(async function () {
      await daoGovernanceToken.mint(addr1.address, ethers.utils.parseEther("10"));
    });

    it("Should not allow non-owner to mint tokens", async function () {
      await expect(daoGovernanceToken.connect(addr1).mint(addr2.address, ethers.utils.parseEther("5")))
        .to.be.revertedWith("Ownable: caller is not the owner");
    });
  });

  describe("Edge Cases and Reverts", function () {
    beforeEach(async function () {
      await daoGovernanceToken.mint(owner.address, ethers.utils.parseEther("10"));
    });

    it("Should revert if minting zero tokens", async function () {
      await expect(daoGovernanceToken.mint(addr2.address, 0))
        .to.be.revertedWith("Cannot mint zero tokens");
    });

    it("Should revert on transfer of insufficient balance", async function () {
      await expect(daoGovernanceToken.connect(owner).transfer(addr1.address, ethers.utils.parseEther("15")))
        .to.be.revertedWith("ERC20: transfer amount exceeds balance");
    });
  });
});